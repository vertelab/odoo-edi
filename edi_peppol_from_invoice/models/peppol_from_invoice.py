#from datetime import date, datetime
#import datetime
#import os, logging, csv, inspect
#from jmespath import search
#from lxml.etree import Element, SubElement, QName, tostring
#from lxml.isoschematron import Schematron

import logging, inspect, datetime

from lxml import etree, objectify
from numpy import percentile

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
        """
        _logger.error("Now returning the ir.actions.act_window!")
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.currency",
            "views": [[False, "tree"], [False, "form"]],
            "target": "new",
            "domain": [("id", "=", "18")],
        }
        """
        # TODO: Remove all currently existing informatoin from the account.move, which the export is to create itself.

        #Basic Fields
        self.set_odoo_data(tree, 'account.move.invoice_date', 
                          xmlpath='/ubl:Invoice/cbc:IssueDate')
        self.set_odoo_data(tree, 'account.move.invoice_date_due', 
                           '/ubl:Invoice/cbc:DueDate')
        self.set_odoo_data(tree, 'account.move.currency_id',
                           text=self.get_currency_by_name())

        #Check own Company
        correct_company = self.is_company_info_correct(tree, 'account.move.company_id', 
                                                       xmlpath='/ubl:Invoice/cac:AccountingCustomerParty/cac:Party')
        if correct_company != True:
            return self.user_choice_window("Could not confirm this invoice is for this company.")

        #Check and import Partner Company
        partner_id = self.find_company_id(tree, 
                                          xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if partner_id is None:
            return self.user_choice_window("Could not find selling company in the database.")
        self.set_odoo_data(tree, 'account.move.partner_id', 
                           text=partner_id)    
        correct_company = self.is_company_info_correct(tree, 'account.move.partner_id', 
                                                       xmlpath='/ubl:Invoice/cac:AccountingSupplierParty/cac:Party')
        if correct_company != True:
            return self.user_choice_window("Found discrepency between the data of the selling company in the invoice, " + 
                                           "and the selling company in the database.")                   

        # Check and import item lines.
        # TODO: Currently this line is created independently of product.product. There should be a link there. Also, make the 'inköp' module a dependancy, and get the producer/sellers-id pair from there.
        for xmlline in self.xpf(tree, '/ubl:Invoice/cac:InvoiceLine'):
            try:
                quantity = float(self.xpft(xmlline, './cbc:InvoicedQuantity'))
                unit_price = float(self.xpft(xmlline, './cac:Price/cbc:PriceAmount')) 
                line = self.env['account.move.line'].with_context({'check_move_validity': False}).create(
                                                         {'move_id': self.id,
                                                          'quantity': quantity, #TODO: Add the 'type' of quantity. (For example: It coudl be 'hours', or 'liters' or anything like that.)
                                                          'name': self.xpft(xmlline, './cac:Item/cbc:Name'), #TODO: This should be description, not 'name'.
                                                          #TODO: This line should move over the name of the item
                                                          #TODO: This line should convert the taxes into the odoo tax tags
                                                          'account_id': 1253, #TODO: This is hard coded to be intra-sweden item purchases. Should be made dynamic.
                                                          'price_unit': unit_price,
                                                          #'discount': 0,
                                                          'tax_ids': self.get_vat_id(self.xpft(xmlline, './cac:Item/cac:ClassifiedTaxCategory/cbc:Percent'))
                                                          })    
            except Exception as e:
                _logger.exception(e)
                raise
        
        # Add any vat journal lines
        # TODO: This must still be done.
        #       Do a search for each existant tax_ids, make a list of them, 
        #       then run through that list creating/adjusting each '2640 Ingående moms' journal line as nessesary, 
        #       for which you get the value by doing a strict 'search' and then multiplying the gotten value with the tax id's percentage..

        # Creates/Adjusts the journal line for '2440 Leverantörskulder' which is nessesary in the swedish system. This can be done automaticly by Odoo, as seen if any of of the journal lines are edited manual.
        #   I am however unable to located this automatic function, and hence this is done manually.
        #   TODO: This should be made to use other existing function, as described in the comment above.
        total_credit = 0
        for lines in self.env['account.move.line'].search([('move_id', '=', self.id),('account_id', '=', 1253)]):          
            total_credit += lines.debit - lines.credit

        existing_debt_journal_lines = self.env['account.move.line'].search([('move_id', '=', self.id),('account_id', '=', 1242)])
        if existing_debt_journal_lines:
            existing_debt_journal_lines[0].write({'move_id': self.id,
                                                 'credit': total_credit,
                                                 'account_id': 1242, #1242 is the id for the 2440 account. #TODO: This is hard coded to work for the swedish system. Should be made dynamic.
                                                 'exclude_from_invoice_tab': True,
                                                 'is_rounding_line': True,
                                                 'date_maturity': self.xpft(tree, '/ubl:Invoice/cbc:DueDate'),
                                                 'partner_id': self.getfield('account.move.partner_id').id,
                                                })
        else:
            self.env['account.move.line'].create(
                                                                                            {'move_id': self.id,
                                                                                            'credit': total_credit,
                                                                                            'account_id': 1242, #1242 is the id for the 2440 account. #TODO: This is hard coded to work for the swedish system. Should be made dynamic.
                                                                                            'exclude_from_invoice_tab': True,
                                                                                            'is_rounding_line': True,
                                                                                            'date_maturity': self.xpft(tree, '/ubl:Invoice/cbc:DueDate'),
                                                                                            'partner_id': self.getfield('account.move.partner_id').id
                                                                                            })