#from datetime import date, datetime
#import datetime
#import os, logging, csv, inspect
#from jmespath import search
#from lxml.etree import Element, SubElement, QName, tostring
#from lxml.isoschematron import Schematron

import logging, inspect, datetime
from cffi import VerificationError


from lxml import etree, objectify
from numpy import percentile

from odoo.exceptions import ValidationError
from odoo import models, api, _, fields
from odoorpc import ODOO


_logger = logging.getLogger(__name__)

"""
class NSMAPS:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, 'ubl':empty}

    XNS={'cac':cac,   
         'cbc':cbc,
         'ubl':empty}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}
"""


# This class handles spesificly the conversion of a Odoo Invoice, to a PEPPOL Invoice.
class Peppol_From_Invoice(models.Model):
    _name = "peppol.frominvoice"
    _inherit = "peppol.frompeppol"
    _description = "Module for importing invoices from PEPPOL to Odoo"



    #Base function for importing a Odoo Invoice, from a PEPPOL Invoice.
    def import_invoice(self, tree):
        # TODO: Remove all currently existing informatoin from the account.move, which the export is to create itself.

        
        #Check own Company
        correct_company, missmached_info = self.is_company_info_correct(tree, 'account.move.company_id', 
                                                       xmlpath='/ubl:Invoice/cac:AccountingCustomerParty/cac:Party')
        if correct_company != True:
            raise ValidationError("The company this invoice is made out to, contains missmatch to the information your company has. \n" +
                                  "The missmatch was between: " + "\n" + 
                                  f"{missmached_info[0][0]}" + ": " + f"{missmached_info[0][1]}" + 
                                  "\n" + "And" + "\n" +
                                  f"{missmached_info[1][0]}" + ": " + f"{missmached_info[1][1]}")
            #return self.user_choice_window("Could not confirm this invoice is for this company.")

        #Check and import Partner Company
        partner_id = self.find_company_id(tree, 
                                          xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if partner_id is None:
            _logger.error(inspect.currentframe().f_code.co_name + ":Could not find the selling company: " + 
                          f"{tree.xpft(xmlline, '/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')}")
            raise ValidationError("This invoice is convering the company: " + 
                                  self.xpft(tree, '/ubl:Invoice/cac:AccountingSupplierParty/cac:Party') + "\n" +
                                  "But no such company could found in the database.")
            #return self.user_choice_window("Could not find selling company in the database.")
        self.set_odoo_data(tree, 'account.move.partner_id', 
                           text=partner_id)    
        correct_company, missmached_info  = self.is_company_info_correct(tree, 'account.move.partner_id', 
                                                       xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if correct_company != True:
            _logger.error(inspect.currentframe().f_code.co_name + "Found discrepency between the data of the selling company in the invoice, " + 
                                           "and the selling company in the database.")        
            raise ValidationError("The company this invoice is from, contains missmatch to the information of said company in the database. \n" +
                                  "The missmatch was between: " + "\n" + 
                                  f"{missmached_info[0][0]}" + ": " + f"{missmached_info[0][1]}" +
                                  "\n" + "And" + "\n" +
                                  f"{missmached_info[1][0]}" + ": " + f"{missmached_info[1][1]}")
            #return self.user_choice_window("Found discrepency between the data of the selling company in the invoice, " + 
            #                               "and the selling company in the database.")                   

        #Basic Fields
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
        
        # Check and import item lines.
        warned_for_missing_product = False
        for xmlline in self.xpf(tree, '/ubl:Invoice/cac:InvoiceLine'):
            try:
                quantity = float(self.xpft(xmlline, './cbc:InvoicedQuantity'))
                unit_price = float(self.xpft(xmlline, './cac:Price/cbc:PriceAmount')) 
                sellers_item = self.xpft(xmlline, './cac:Item/cac:SellersItemIdentification/cbc:ID')

                # TODO: Only products that have no variants are handled by this code. 
                # It should be changed to be able to handle products with multible variants.
                supplierinfo = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id),('product_code', '=', sellers_item)])
                product = self.env['product.product'].search([('product_tmpl_id', '=', supplierinfo.product_tmpl_id.id)])
                if len(product) == 0:
                    raise ValidationError("Could not find the item from the invoice in the products database.\n" +
                                          "Please ensure there the product with the sellers id of: " + f"{sellers_item}" + "\n"
                                          "Is buyable from the company: " + f"{self.partner_id.name}")
                if len(product) > 1:
                    raise ValidationError("More then one products with the matching product code was found." + "\n" +
                                          "Are varient products used? These are not yet handled.")

                line = self.env['account.move.line'].with_context({'check_move_validity': False}).create(
                                                        {'move_id': self.id,
                                                        'quantity': quantity, #TODO: Add the 'type' of quantity. (For example: It coudl be 'hours', or 'liters' or anything like that.)
                                                        'account_id': 1253, #TODO: This is hard coded to be intra-sweden item purchases. Should be made dynamic.
                                                        'recompute_tax_line': True,
                                                        'product_id': product.id
                                                        })
                _logger.warning(f"{line.product_id=}")
                _logger.warning(f"{line._get_computed_price_unit()=}")    
                line.with_context({'check_move_validity': False})._onchange_product_id()

                product_correct, missmached_info = self.is_product_info_correct(line, xmlline)
                if not product_correct:
                    raise ValidationError("The product: " + line.name + " had a missmatch between the database, and the invoice. \n" +
                                          "The missmatch was between: " + "\n" + 
                                          f"{missmached_info[0][0]}" + ": " + f"{missmached_info[0][1]}" +
                                          "\n" + "And" + "\n" +
                                          f"{missmached_info[1][0]}" + ": " + f"{missmached_info[1][1]}")
                continue      

                # If the search for a item failed add the line manualy instead.
                #_logger.warning(inspect.currentframe().f_code.co_name + ": Could not find the item: " + f"{sellers_item=}" + " in the product.product database and adding this account.move.invoice without a linked product.product instead.")
                #line = self.env['account.move.line'].with_context({'check_move_validity': False}).create(
                #                                         {'move_id': self.id,
                #                                          'quantity': quantity, #TODO: Add the 'type' of quantity. (For example: It coudl be 'hours', or 'liters' or anything like that.)
                #                                          'name': self.xpft(xmlline, './cac:Item/cbc:Name'), #TODO: This should be description, not 'name'.
                #                                         #TODO: This line should move over the name of the item
                #                                         #TODO: This line should convert the taxes into the odoo tax tags
                #                                          'account_id': 1253, #TODO: This is hard coded to be intra-sweden item purchases. Should be made dynamic.
                #                                          'price_unit': unit_price,
                #                                          'tax_ids': self.get_vat_id(self.xpft(xmlline, './cac:Item/cac:ClassifiedTaxCategory/cbc:Percent')),
                #                                          'recompute_tax_line': True,
                #                                          #'payment_reference': self.xpft(tree, '/ubl:Invoice/cbc:ID'),
                #                                          })     

                # Updates the tax lines.      
                #line.with_context({'check_move_validity': False})._onchange_product_id()
                #line.with_context({'check_move_validity': False})._onchange_mark_recompute_taxes()                                      
            except Exception as e:
                _logger.exception(e)
                raise
            
        # Adds/updates the '2440 Leverantörskuld' which balances the invoice, as well as the tax line due to 'True' being inputet.
        self.with_context({'check_move_validity': False})._recompute_dynamic_lines(True)
        
        # TODO: Add check here for if the total prices and total taxes and such, do not match.
        # If so, remove everything, then throw a error to the user. 
        #invoice_correct, missmached_info = self.is_invoice_info_correct(tree)
        #if not product_correct:
        #    raise ValidationError("The invoice had a missmatch between what was converted, and the invoice. \n" +
        #                          "The missmatch was between: " + "\n" + 
        #                          f"{missmached_info[0][0]}" + ": " + f"{missmached_info[0][1]}" +
        #                          "\n" + "And" + "\n" +
        #                          f"{missmached_info[1][0]}" + ": " + f"{missmached_info[1][1]}")

        """
        total_credit = 0
        for lines in self.env['account.move.line'].search([('move_id', '=', self.id),('account_id', '=', 1253)]):          
            total_credit += lines.debit - lines.credit

        existing_debt_journal_lines = self.env['account.move.line'].search([('move_id', '=', self.id),('account_id', '=', 1242)])
        balancing = {'move_id': self.id,
                     'credit': total_credit,
                     'account_id': 1242, #1242 is the id for the 2440 account. #TODO: This is hard coded to work for the swedish system. Should be made dynamic.
                     'exclude_from_invoice_tab': True,
                     'is_rounding_line': True,
                     'date_maturity': self.xpft(tree, '/ubl:Invoice/cbc:DueDate'),
                     'partner_id': self.getfield('account.move.partner_id').id,
                    }
        if existing_debt_journal_lines:
            existing_debt_journal_lines[0].write(balancing)
        else:
            self.env['account.move.line'].create(balancing)
        """
        