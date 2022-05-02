import logging
from odoo import models, api, _, fields

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring

_logger = logging.getLogger(__name__)

class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.toinvoice", "peppol.toorder", "peppol.frominvoice"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."


    def to_peppol_button(self):
        self.to_peppol()
        return None

    def from_peppol_button(self):
        self.from_peppol()
        return None
  
    def to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())
        #self.env['peppol.toinvoice'].create_invoice())
        #_logger.warning("XML has ID: " + tree.xpath('/Invoice/cbc:ID/text()', namespaces=XNS)[0])
        #tree = etree.ElementTree(self.create_order())
        
        tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

        #_logger.error(inspect.currentframe().f_code.co_name + ": " + "NO VALIDATION IS DONE!")
        #_logger.warning("Starting validation attemps")

        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml')

    def from_peppol(self):
        tree = self.parse_xml('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        if tree is None:
            return None

        self.import_invoice(tree)
