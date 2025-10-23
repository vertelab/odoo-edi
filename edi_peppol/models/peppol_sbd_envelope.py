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
        doc_id_elem = root.find('.//sbd:StandardBusinessDocumentHeader/sbd:DocumentIdentification/sbd:Type',
                                namespaces=NS)
        documentIdentification_type = doc_id_elem.text if doc_id_elem is not None else None

        if not documentIdentification_type:
            self.state = "error"
            return

        # Find the payload by documentIdentification_type tag
        payload_tag = documentIdentification_type.split(':')[
            -1] if ':' in documentIdentification_type else documentIdentification_type
        print(f"Looking for payload tag: {payload_tag}")

        # Try to find the payload element - it might be in a different namespace
        # First, try without namespace
        payload_elem = root.find(f"./{payload_tag}")

        # If not found, search through all child elements regardless of namespace
        if payload_elem is None:
            for child in root:
                # Check if the local name (without namespace) matches
                if child.tag.endswith(payload_tag) or child.tag.split('}')[-1] == payload_tag:
                    payload_elem = child
                    break

        print(f"Found payload_elem: {payload_elem}")

        if payload_elem is not None:
            # Get the original XML string from the binary payload
            binary_data = base64.b64decode(self.payload)
            original_xml_string = binary_data.decode('utf-8')

            # Find the start and end of the payload element in the original string
            # Look for the opening tag (with any namespace prefix)
            import re
            # Match opening tag like <Catalogue or <prefix:Catalogue
            pattern = rf'<(?:\w+:)?{payload_tag}[>\s]'
            match = re.search(pattern, original_xml_string)

            if match:
                start_pos = match.start()
                # Find the corresponding closing tag
                closing_pattern = rf'</(?:\w+:)?{payload_tag}>'
                closing_match = re.search(closing_pattern, original_xml_string[start_pos:])

                if closing_match:
                    end_pos = start_pos + closing_match.end()
                    payload_str = original_xml_string[start_pos:end_pos]

                    # Encode to base64 for binary field
                    payload_binary = base64.b64encode(payload_str.encode('utf-8'))

                    self.env['edi.message'].create({
                        'payload': payload_binary,
                        'envelope_id': self.id,
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
