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


    def log_element(self, ele, msg='', verbose=False):
        if len(ele) == 0:
            if verbose:
                _logger.warning(inspect.currentframe().f_code.co_name + ": " + "No element found to print!")
        elif len(ele) > 1:
            if verbose:
                _logger.warning(inspect.currentframe().f_code.co_name + ": " + "More then one element found to print!")
        else:
            str = "Elment Tag: " + ele[0].tag
            if ele[0].text is not None:
                str =+ "  | Element Text: " + ele[0].text
            _logger.warning(msg + str)


    def convert_to_string(self, value):
        #_logger.warning(f"{type(value)=}")
        if isinstance(value, str):
            return value
        elif isinstance(value, datetime.date):
            return value.strftime("%Y-%m-%d")
        elif isinstance(value, float):
            return str(round(value,2))

        _logger.error(inspect.currentframe().f_code.co_name + ": " + "Type of variable is not being handled like it should!")
        return None