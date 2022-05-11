import logging, inspect, datetime
from cffi import VerificationError

from lxml import etree, objectify
from numpy import percentile

from odoo.exceptions import ValidationError
from odoo import models, api, _, fields
from odoorpc import ODOO

_logger = logging.getLogger(__name__)


# This class handles spesificly the conversion of a Odoo Invoice, to a PEPPOL Invoice.
class Peppol_From_Invoice(models.Model):
    _name = 'peppol.frominvoice'
    _inherit = 'peppol.frompeppol'
    _description = 'Module for importing invoices from PEPPOL to Odoo'

    #Base function for importing a Odoo Invoice, from a PEPPOL Invoice.
    def import_invoice(self, tree):
        # TODO: Remove all currently existing informatoin from the account.move, which the export is to create itself.

        # Checks that this invoice has the users current company as the 'Customer'
        #  and that the information the invoice has and the database
        #  has about the own company are the same.
        correct_company, missmached_info = self.is_company_info_correct(tree, 'account.move.company_id', 
                                                       xmlpath='/ubl:Invoice/cac:AccountingCustomerParty/cac:Party')
        if correct_company != True:
            raise ValidationError('The company this invoice is made out to, contains missmatch to the information your company has. \n' +
                                  'The missmatch was between: ' + '\n' + 
                                  f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' + 
                                  '\n' + 'And' + '\n' +
                                  f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')

        # Checks that this invoice has the same info about the 'Supplying' company
        #  as the database has.
        #  Also imports the 'Supplying' companies ID.
        partner_id = self.find_company_id(tree, 
                                          xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if partner_id is None:
            _logger.error(inspect.currentframe().f_code.co_name + ':Could not find the selling company: ' + 
                          f"{tree.xpft(xmlline, '/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')}")
            raise ValidationError('This invoice is convering the company: ' + 
                                  self.xpft(tree, '/ubl:Invoice/cac:AccountingSupplierParty/cac:Party') + '\n' +
                                  'But no such company could found in the database.')
        self.set_odoo_data(tree, 'account.move.partner_id', 
                           text=partner_id)

        correct_company, missmached_info  = self.is_company_info_correct(tree, 'account.move.partner_id', 
                                                       xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if correct_company != True:
            _logger.error(inspect.currentframe().f_code.co_name + 'Found discrepency between the data of the selling company in the invoice, ' + 
                                           'and the selling company in the database.')        
            raise ValidationError('The company this invoice is from, contains missmatch to the information of said company in the database. \n' +
                                  'The missmatch was between: ' + '\n' + 
                                  f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' +
                                  '\n' + 'And' + '\n' +
                                  f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')


        # Simple fields that require no conversion.
        self.set_odoo_data(tree, 'account.move.invoice_date', 
                           xmlpath='/ubl:Invoice/cbc:IssueDate')
        self.set_odoo_data(tree, 'account.move.invoice_date_due', 
                           xmlpath='/ubl:Invoice/cbc:DueDate')
        self.set_odoo_data(tree, 'account.move.currency_id',
                           text=self.get_currency_by_name())
        self.set_odoo_data(tree, 'account.move.ref',
                           xmlpath='/ubl:Invoice/cbc:ID')
        self.set_odoo_data(tree, 'account.move.narration',
                           xmlpath='/ubl:Invoice/cac:PaymentTerms/cbc:Note')        
        
        # Checks and import item lines.
        for xmlline in self.xpf(tree, '/ubl:Invoice/cac:InvoiceLine'):
            try:
                quantity = float(self.xpft(xmlline, './cbc:InvoicedQuantity'))
                unit_price = float(self.xpft(xmlline, './cac:Price/cbc:PriceAmount')) 
                sellers_item = self.xpft(xmlline, './cac:Item/cac:SellersItemIdentification/cbc:ID')

                # TODO: Only products that have no variants are handled by this code. 
                #  It should be changed to be able to handle products with multible variants.
                supplierinfo = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id),('product_code', '=', sellers_item)])
                product = self.env['product.product'].search([('product_tmpl_id', '=', supplierinfo.product_tmpl_id.id)])
                if len(product) == 0:
                    raise ValidationError('Could not find the item from the invoice in the products database.\n' +
                                          'Please ensure there the product with the sellers id of: ' + f'{sellers_item}' + '\n'
                                          'Is buyable from the company: ' + f'{self.partner_id.name}')
                if len(product) > 1:
                    raise ValidationError('More then one products with the matching product code was found.' + '\n' +
                                          'Are varient products used? These are not yet handled.')

                # Creates the new line, with 'simple' fields filled in
                line = self.env['account.move.line'].with_context({'check_move_validity': False}).create(
                                                        {'move_id': self.id,
                                                        'quantity': quantity, #TODO: Add the 'type' of quantity. (For example: It coudl be 'hours', or 'liters' or anything like that.)
                                                        'account_id': 1253, #TODO: This is hard coded to be intra-sweden item purchases. Should be made dynamic.
                                                        'recompute_tax_line': True,
                                                        'product_id': product.id
                                                        })
                # Imports item information from the database, relying on the 'product_id' 
                line.with_context({'check_move_validity': False})._onchange_product_id()
                # Checks that there is no missmatch between what is in the database about a item
                #  and what is actually writen in the incomming invoice
                product_correct, missmached_info = self.is_product_info_correct(line, xmlline)
                if not product_correct:
                    raise ValidationError('The product: ' + line.name + ' had a missmatch between the database, and the invoice. \n' +
                                          'The missmatch was between: ' + '\n' + 
                                          f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' +
                                          '\n' + 'And' + '\n' +
                                          f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')                             
            except Exception as e:
                _logger.exception(e)
                raise
            
        # Adds/updates the '2440 Leverantörskuld' which balances the invoice, as well as the tax line due to 'True' being inputet.
        self.with_context({'check_move_validity': False})._recompute_dynamic_lines(True)
        
        # TODO: Add check here for if the total prices and total taxes and such, do not match.
        # If so, remove everything, then throw a error to the user. 
        #invoice_correct, missmached_info = self.is_invoice_info_correct(tree)
        #if not product_correct:
        #    raise ValidationError('The invoice had a missmatch between what was converted, and the invoice. \n' +
        #                          'The missmatch was between: ' + '\n' + 
        #                          f'{missmached_info[0][0]}' + ': ' + f'{missmached_info[0][1]}' +
        #                          '\n' + 'And' + '\n' +
        #                          f'{missmached_info[1][0]}' + ': ' + f'{missmached_info[1][1]}')