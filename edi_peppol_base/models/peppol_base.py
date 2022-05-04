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

class NSMAPS:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, None:empty}

    XNS={'cac':cac,   
         'cbc':cbc}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}

class Peppol_Base(models.TransientModel):
    _name = "peppol.base"
    _description = "Base module which contains functions to assist in converting between PEPPOL and Odoo."

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
    
    def translate_tax_category_to_peppol(self, input):
        tax_category_dict = {
            "MP1" : "S",
            "MP1i" : "S",
            "MP2" : "S",
            "MP2i" : "S",
            "MP3" : "S",
            "MP3i" : "S",
            "MF" : "Z",
            "FVEU0" : "Z",
            "FVUEU0" : "Z"
        }
        output = None
        try:
            output = tax_category_dict[input]       
        except:
            _logger.error(inspect.currentframe().f_code.co_name + 
                          ": Tax code of " + 
                          str(f"{input=}") + 
                          " could not be translated!")
        return output

    def user_choice_window(self, msg="No message text given!", state=None):
        #text = "This message is about own company info disparity!"
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
            'res_id': value.id
        }
    
    def getfield(self, lookup, inst=None):

        if lookup is None:
            return None

        if inst is None:
            inst = self

        l = lookup.split(',', 1)
        current_module = l[0].rsplit('.', 1)[0] 
        current_field_name = l[0].rsplit('.', 1)[1]
        try:
            current_field_value = inst[current_field_name]
        except:
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + 
                            "exception found when trying to find: " + 
                            f"{current_field_name=}" + " for inst: " + 
                            str(f"{inst=}"))
            return None

        if len(l) == 1:
            return current_field_value
        else:
            ln = l[1].split(',', 1)
            next_module = ln[0].rsplit('.', 1)[0] 
            inst = inst.env[next_module].browse(current_field_value.id)  
            return self.getfield(l[1], inst)    