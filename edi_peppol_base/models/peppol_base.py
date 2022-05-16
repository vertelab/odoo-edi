#from datetime import date, datetime
import datetime
import os, logging, csv, inspect
from jmespath import search

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring
from lxml.isoschematron import Schematron
from odoo import models, api, _, fields
from odoorpc import ODOO

#from peppol_invoice_from_odoo import create_invoice
#from edi_peppol_validate import validate_peppol

#from lxml import etree, html

_logger = logging.getLogger(__name__)

# XML namespace class for the 'From PEPPOL' use.
class NSMAPFC:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, 'ubl':empty}

    XNS={'cac':cac,
         'cbc':cbc,
         'ubl':empty}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}

# XML namespace class for the 'To PEPPOL' use.
class NSMAPTC:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, None:empty}

    XNS={'cac':cac,
         'cbc':cbc}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}

# Class containing functions that all Peppol Modules may need to use.
class Peppol_Base(models.Model):
    _name = "peppol.base"
    _description = ("Base module which contains functions " +
                    "to assist in converting between PEPPOL and Odoo.")

    # Helperfunction to access the NSMAPF class
    def nsmapf(self):
        return NSMAPFC

    # Helperfunction to access the NSMAPF class
    def nsmapt(self):
        return NSMAPTC

    # Converts the inputet value to a string.
    # TODO: Is this decrepit?
    def convert_to_string(self, value):
        if isinstance(value, str):
            return value
        elif isinstance(value, datetime.date):
            return value.strftime("%Y-%m-%d")
        elif isinstance(value, float):
            return str(round(value,2))
        elif isinstance(value, int):
            return str(value)

        _logger.error(inspect.currentframe().f_code.co_name +
                      ": Variable of type " + str(f"{type(value)}") +
                      " is not being handled like it should!")
        return None

    # Translates the base swedish vat-taxes, from Odoo into PEPPOL format.
    # TODO: Add more kinds of vat-acounts.
    def translate_tax_category_to_peppol(self, input):
        tax_category_dict = {
            'MP1' : 'S',
            'MP2' : 'S',
            'MP3' : 'S',
            'MF' : 'Z',
            'FVEU0' : 'Z',
            'FVUEU0' : 'Z',
        }
        output = None
        try:
            output = tax_category_dict[input]
        except:
            _logger.error(inspect.currentframe().f_code.co_name +
                          ": Tax code of " +
                          str(f"{input=}") +
                          " could not be translated into PEPPOL format!")
        return output

    # Translates the base swedish vat-taxes, from PEPPOL format into Odoo.
    # Todo, add more detailed translation, which leads to other vat-codes then just I's
    def translate_tax_category_from_peppol(self, input):
        tax_category_dict = {
            '25.0' : 'I',
            '12.0' : 'I12',
            '6.0' : 'I6',
        }
        if input is None:
            return None

        output = None
        try:
            output = tax_category_dict[input]
        except:
            _logger.error(inspect.currentframe().f_code.co_name +
                          ": Tax code of " +
                          str(f"{input=}") +
                          " could not be translated into Odoo format!")
        return output

    # A wizard to display a popup to the user and allow them to make choices.
    # TODO: Is this decrepit and could be removed?
    def user_choice_window(self, msg="No message text given!", state=None):
        query ='delete from peppol_wizard'
        self.env.cr.execute(query)
        value = self.env['peppol.wizard'].sudo().create({'text':msg, 'state':state})
        return {
            #"name": "WizardTest",
            'type': 'ir.actions.act_window',
            'name': 'Peppol Message',
            'res_model': 'peppol.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            #"views": [[False, "tree"], [False, "form"]],
            'target': 'new',
            #"domain": [("amount_total_signed", "!=", "0")],
            'res_id': value.id,
        }

    # xpath command for the 'From odoo' way
    # xpf stands for: 'XPath From'
    def xpf(self, tree, path):
        return tree.xpath(path, namespaces=self.nsmapf().XNS)

    # xpath command for the 'From odoo' way which returns the first found elements text
    # xpft stands for: 'XPath From Text'
    def xpft(self, tree, path):
        try:
            return self.xpf(tree, path)[0].text
        except BaseException as e:
            _logger.error(inspect.currentframe().f_code.co_name + ": " +
                          "Exception when trying to find text for: " +
                            f"{path=}" + " with the exception: " +
                            f"{e=}")

    #xpath command for the 'To odoo' way
    # xpf stands for: 'XPath To'
    def xpt(self, tree, path):
        return tree.xpath(path, namespaces=self.nsmapt().XNS)