# ~ #This file is going to add the functions neeeded to fold/unfold envelope and pack/unpack messages.
# ~ from odoo import api, fields, models, tools,_
# ~ from odoo.exceptions import UserError
# ~ from odoo.tools.safe_eval import safe_eval

# ~ import logging
# ~ _logger = logging.getLogger(__name__)

# ~ import base64
# ~ import xml.etree.ElementTree as ET
# ~ import xmltodict
# ~ # xml_string is your XML content as a string




# ~ class EdiEnvelope(models.Model):
    # ~ _inherit = 'edi.envelope'
    
    # ~ type = fields.Selection(selection_add=[('sbd','StandardBusinessDocument')])
    # ~ def get_receiver_sender(self,sbd_dict):
        # ~ sender_vals = (sbd_dict.get('StandardBusinessDocument', {})
                  # ~ .get('StandardBusinessDocumentHeader', {})
                  # ~ .get('Sender', {})
                  # ~ .get('Identifier', {})
                  # ~ .get('#text'))
                  
        # ~ if sender_vals:
           # ~ sender_partner = self.env['res.partner'].search([('peppol_eas','=',sender_vals.split(":")[0]),('peppol_endpoint','=',sender_vals.split(":")[1])])
           # ~ if not sender_partner:
               # ~ sender_partner = self.env['res.partner'].create(
               # ~ {
               # ~ 'peppol_eas':sender_vals.split(":")[0],
               # ~ 'peppol_endpoint':sender_vals.split(":")[1],
               # ~ 'company_type':'company',
               # ~ 'name':sender_vals,
               # ~ })
                  
        # ~ receiver_vals = (sbd_dict.get('StandardBusinessDocument', {})
                  # ~ .get('StandardBusinessDocumentHeader', {})
                  # ~ .get('Receiver', {})
                  # ~ .get('Identifier', {})
                  # ~ .get('#text', ''))
        # ~ receiver_partner = self.env['res.partner'].search([('peppol_eas','=',receiver_vals.split(":")[0]),('peppol_endpoint','=',receiver_vals.split(":")[1])])
        # ~ if not receiver_partner:
               # ~ receiver_partner = self.env['res.partner'].create(
               # ~ {
               # ~ 'peppol_eas':receiver_vals.split(":")[0],
               # ~ 'peppol_endpoint':receiver_vals.split(":")[1],
               # ~ 'company_type':'company',
               # ~ 'name':sender_vals,
               # ~ })
        # ~ self.sender = sender_partner
        # ~ self.receiver = receiver_partner
        

    # ~ def unfold(self, existing_invoice=None):
        # ~ """Process the envelope and create messages"""
        # ~ """Test other unpack functions"""
        # ~ result = super().unfold()
        # ~ if not result:
            # ~ try:
                # ~ if self.payload:
                    # ~ binary_data = base64.b64decode(self.payload)
                    # ~ xml_string = binary_data.decode('utf-8')
                    # ~ sbd_dict = xmltodict.parse(xml_string)
                    # ~ _logger.warning(f"{sbd_dict=}")
                    # ~ if sbd_dict.get("StandardBusinessDocument"):
                       # ~ self.type = "sbd"
                    # ~ else:
                       # ~ return False
                    # ~ self.get_receiver_sender(sbd_dict)
                    


            # ~ except Exception as e:
                # ~ raise e
                # ~ _logger.warning(e)
           
        # ~ return result




