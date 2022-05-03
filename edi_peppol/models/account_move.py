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
        return self.from_peppol()
  
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

        return self.user_choice_window()

        self.import_invoice(tree)

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



    """
    def btn_show_dialog_box(self):
        text = "THIS IS MY SPECIAL MESSAGE!"
        query ='delete from display_dialog_box'
        self.env.cr.execute(query)
        value = self.env['display.dialog.box'].sudo().create({'text':text})
        return{
            'type':'ir.actions.act_window',
            'name':'Message',
            'res_model':'display.dialog.box',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'res_id':value.id                
        }

            "type": "ir.actions.act_window",
            "res_model": "res.currency",
            "views": [[False, "tree"], [False, "form"]],
            "target": "new",
            "domain": [("id", "=", "18")],     
    """
