from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import logging
import base64
import xml.etree.ElementTree as ET
import re

_logger = logging.getLogger(__name__)


class EdiEnvelope(models.Model):
    _inherit = 'edi.envelope'

    type = fields.Selection(selection_add=[('sbd', 'StandardBusinessDocument')])

    def _find_or_create_partner(self, partner_vals, search_domain=None):
        """
        Find or create a partner based on values.
        Reusable utility method.

        :param partner_vals: Dictionary of partner values
        :param search_domain: Optional custom search domain
        :return: res.partner record
        """
        if not search_domain:
            search_domain = [
                ('peppol_eas', '=', partner_vals.get('peppol_eas')),
                ('peppol_endpoint', '=', partner_vals.get('peppol_endpoint'))
            ]

        partner = self.env['res.partner'].search(search_domain, limit=1)

        if not partner:
            partner = self.env['res.partner'].create(partner_vals)
            _logger.info(f"Created partner: {partner_vals.get('name')}")

        return partner

    def _extract_sbdh_party(self, root, party_type='Sender'):
        """
        Extract party information from StandardBusinessDocumentHeader.

        :param root: XML root element
        :param party_type: 'Sender' or 'Receiver'
        :return: res.partner record or False
        """
        NS = {'sbd': 'http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader'}

        # Find party identifier
        party_elem = root.find(
            f'.//sbd:StandardBusinessDocumentHeader/sbd:{party_type}/sbd:Identifier',
            namespaces=NS
        )

        if party_elem is None or not party_elem.text:
            _logger.warning(f"No {party_type} identifier found in SBDH")
            return False

        party_vals = party_elem.text

        # Parse the identifier (format: "eas:endpoint")
        if ':' in party_vals:
            eas, endpoint = party_vals.split(":", 1)
        else:
            _logger.warning(f"Invalid {party_type} identifier format: {party_vals}")
            return False

        # Prepare partner values
        partner_vals = {
            'peppol_eas': eas,
            'peppol_endpoint': endpoint,
            'company_type': 'company',
            'name': party_vals,  # Use full identifier as name initially
        }

        return self._find_or_create_partner(partner_vals)

    def get_receiver_sender(self, root):
        """Extract sender and receiver from StandardBusinessDocumentHeader"""

        sender_partner = self._extract_sbdh_party(root, 'Sender')
        receiver_partner = self._extract_sbdh_party(root, 'Receiver')

        self.sender = sender_partner
        self.receiver = receiver_partner

    def _extract_payload_from_xml(self, root, payload_tag):
        """
        Extract payload element from XML root, preserving original formatting.

        :param root: XML root element
        :param payload_tag: Tag name to search for (without namespace)
        :return: Base64 encoded payload string or False
        """
        # Try to find the payload element
        payload_elem = root.find(f"./{payload_tag}")

        # If not found, search through all children regardless of namespace
        if payload_elem is None:
            for child in root:
                local_tag = child.tag.split('}')[-1]
                if local_tag == payload_tag:
                    payload_elem = child
                    break

        if payload_elem is None:
            _logger.warning(f"Payload element '{payload_tag}' not found")
            return False

        # Get the original XML string from the envelope payload
        binary_data = base64.b64decode(self.payload)
        original_xml_string = binary_data.decode('utf-8')

        # Extract the payload section from original XML to preserve formatting
        # Match opening tag like <Catalogue or <prefix:Catalogue
        pattern = rf'<(?:\w+:)?{payload_tag}[>\s]'
        match = re.search(pattern, original_xml_string)

        if not match:
            _logger.warning(f"Could not find opening tag for '{payload_tag}' in original XML")
            return False

        start_pos = match.start()

        # Find the corresponding closing tag
        closing_pattern = rf'</(?:\w+:)?{payload_tag}>'
        closing_match = re.search(closing_pattern, original_xml_string[start_pos:])

        if not closing_match:
            _logger.warning(f"Could not find closing tag for '{payload_tag}'")
            return False

        end_pos = start_pos + closing_match.end()
        payload_str = original_xml_string[start_pos:end_pos]

        # Encode to base64 for binary field
        return base64.b64encode(payload_str.encode('utf-8'))

    def create_edi_message(self, root):
        """Create EDI message from StandardBusinessDocument payload"""

        NS = {'sbd': 'http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader'}

        # Find DocumentIdentification Type
        doc_id_elem = root.find(
            './/sbd:StandardBusinessDocumentHeader/sbd:DocumentIdentification/sbd:Type',
            namespaces=NS
        )

        if doc_id_elem is None or not doc_id_elem.text:
            _logger.error("No DocumentIdentification Type found in SBDH")
            self.state = "error"
            return False

        document_type = doc_id_elem.text

        # Remove namespace prefix if present
        payload_tag = document_type.split(':')[-1]

        _logger.info(f"Extracting payload for document type: {payload_tag}")

        # Extract payload
        payload_binary = self._extract_payload_from_xml(root, payload_tag)

        if payload_binary:
            edi_message_id = self.env['edi.message'].create({
                'payload': payload_binary,
                'envelope_id': self.id,
            })
            edi_message_id.unpack()
            _logger.info(f"Created EDI message for envelope {self.id}")
            self.state = "received"
            return True

        return False

    def unfold(self, existing_invoice=None):
        """Unfold StandardBusinessDocument envelope"""

        result = super().unfold()

        if not result and self.payload:
            try:
                # Decode and parse XML
                binary_data = base64.b64decode(self.payload)
                xml_string = binary_data.decode('utf-8')
                root = ET.fromstring(xml_string)

                _logger.info(f"Parsed XML root tag: {root.tag}")

                # Check if it's a StandardBusinessDocument
                # expected_tag = '{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}StandardBusinessDocument'
                #
                # if root.tag != expected_tag:
                #     _logger.warning(f"Not a StandardBusinessDocument: {root.tag}")
                #     return False
                #
                # # Set envelope type
                # self.type = "sbd"
                #
                # # Extract parties
                # self.get_receiver_sender(root)
                #
                # # Create message
                # self.create_edi_message(root)

                # Check if it's a StandardBusinessDocument (wrapped)
                if 'StandardBusinessDocument' in root.tag:
                    # Set envelope type
                    self.type = "sbd"

                    # Extract parties from SBDH
                    self.get_receiver_sender(root)

                    # Create message from payload inside SBD
                    self.create_edi_message(root)

                else:
                    # Bare UBL document (Catalogue, Invoice, etc.) - no envelope
                    _logger.info(f"Processing bare UBL document: {root.tag}")

                    # For bare documents, create message directly with the entire payload
                    edi_message_id = self.env['edi.message'].create({
                        'payload': self.payload,  # Use the entire payload as-is
                        'envelope_id': self.id,
                    })
                    edi_message_id.unpack()

                    self.state = "received"

                return True

            except Exception as e:
                _logger.error(f"Error unfolding StandardBusinessDocument: {e}")
                raise

        return result