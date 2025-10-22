from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
import logging
import base64
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)

class EdiEnvelope(models.Model):
    _inherit = 'edi.envelope'
    
    type = fields.Selection(selection_add=[('sbd','StandardBusinessDocument')])
    
    def get_receiver_sender(self, root):
        # Find sender identifier text
        NS = {'sbd': 'http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader'}

        sender_elem = root.find('.//sbd:StandardBusinessDocumentHeader/sbd:Sender/sbd:Identifier', namespaces=NS)
        sender_vals = sender_elem.text if sender_elem is not None else None
        sender_partner = False
        receiver_partner = False
        _logger.warning(f"{sender_vals=}")
        if sender_vals:
            sender_eas, sender_endpoint = sender_vals.split(":")
            sender_partner = self.env['res.partner'].search([
                ('peppol_eas', '=', sender_eas),
                ('peppol_endpoint', '=', sender_endpoint)
            ])
            if not sender_partner:
                sender_partner = self.env['res.partner'].create({
                    'peppol_eas': sender_eas,
                    'peppol_endpoint': sender_endpoint,
                    'company_type': 'company',
                    'name': sender_vals,
                })

        # Find receiver identifier text
        receiver_elem = root.find('.//sbd:StandardBusinessDocumentHeader/sbd:Receiver/sbd:Identifier', namespaces=NS)
        receiver_vals = receiver_elem.text if receiver_elem is not None else None
        
        if receiver_vals:
            receiver_eas, receiver_endpoint = receiver_vals.split(":")
            receiver_partner = self.env['res.partner'].search([
                ('peppol_eas', '=', receiver_eas),
                ('peppol_endpoint', '=', receiver_endpoint)
            ])
            if not receiver_partner:
                receiver_partner = self.env['res.partner'].create({
                    'peppol_eas': receiver_eas,
                    'peppol_endpoint': receiver_endpoint,
                    'company_type': 'company',
                    'name': receiver_vals,
                })

        self.sender = sender_partner
        self.receiver = receiver_partner
        
    def create_edi_message(self, root):
        # Find DocumentIdentification type
        NS = {'sbd': 'http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader'}
        doc_id_elem = root.find('.//sbd:StandardBusinessDocumentHeader/sbd:DocumentIdentification/sbd:Type', namespaces=NS)
        documentIdentification_type = doc_id_elem.text if doc_id_elem is not None else None
        
        # ~ doc_id_elem = root.find("./StandardBusinessDocumentHeader/DocumentIdentification/Type")
        # ~ documentIdentification_type = doc_id_elem.text if doc_id_elem is not None else None

        if not documentIdentification_type:
            self.state = "error"
            return
        
        # Find the payload by documentIdentification_type tag
        payload_elem = root.find(f"./sbd:{documentIdentification_type}", namespaces=NS)
        if payload_elem is not None:
            # You can serialize this subtree if needed, example:
            payload_str = ET.tostring(payload_elem, encoding='utf-8').decode('utf-8')
            self.env['edi.message'].create({
                'payload': payload_str,
                'envelope_id':self.id,
            })

    def unfold(self, existing_invoice=None):
        result = super().unfold()
        if not result:
            try:
                if self.payload:
                    binary_data = base64.b64decode(self.payload)
                    xml_string = binary_data.decode('utf-8')
                    root = ET.fromstring(xml_string)
                    _logger.warning(f"Parsed XML root tag: {root.tag}")
                    if root.tag == '{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}StandardBusinessDocument':
                        self.type = "sbd"
                    else:
                        return False
                    self.get_receiver_sender(root)
                    self.create_edi_message(root)
            except Exception as e:
                _logger.warning(e)
                raise e
        return result
