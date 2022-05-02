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

class XMLNamespaces:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"


NSMAP={'cac':XMLNamespaces.cac, 'cbc':XMLNamespaces.cbc, None:XMLNamespaces.empty}

XNS={   'cac':XMLNamespaces.cac,   
        'cbc':XMLNamespaces.cbc}

ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


class Peppol_Base(models.Model):
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


