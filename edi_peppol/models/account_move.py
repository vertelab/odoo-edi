import logging
from odoo import models, api, _, fields

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring


_logger = logging.getLogger(__name__)

class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.toinvoice", "peppol.toorder"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."


    def peppol_button(self):
        _logger.warning("Clicked the Button!")
        _logger.warning(f"{self.name=}")
        #currency_row = self.env["res.currency"].browse(self.currency_id.id)
        #_logger.warning(f"{self.currency_id.name=}")

        #self.test()

        for x in self.invoice_line_ids:
            _logger.warning(x.read())

        self.to_peppol()




        #_logger.warning(peppol_main.main())
        return None

    
    def to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())#self.env['peppol.toinvoice'].create_invoice())
        #_logger.warning("XML has ID: " + tree.xpath('/Invoice/cbc:ID/text()', namespaces=XNS)[0])
        #tree = etree.ElementTree(self.create_order())
        
        tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

        #_logger.error(inspect.currentframe().f_code.co_name + ": " + "NO VALIDATION IS DONE!")
        #_logger.warning("Starting validation attemps")

        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml')