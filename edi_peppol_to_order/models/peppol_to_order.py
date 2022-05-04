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


class Peppol_To_Order(models.Model):
    _name = "peppol.toorder"
    _inherit = ["peppol.topeppol"]
    _description = "Module for converting order from Odoo to PEPPOL"


    def create_order(self):
        invoice = etree.Element("Invoice", nsmap=NSMAPS.NSMAP)

        _logger.warning("Running Create_Order!")

        #Invoice Instructions
        self.convert_field(invoice, 'Invoice', 'Text', 'THIS IS A ORDER TEST!')
        return invoice
