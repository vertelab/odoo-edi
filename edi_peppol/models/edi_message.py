from datetime import datetime

from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)

import base64
import xml.etree.ElementTree as ET
import xmltodict





class EdiMessage(models.Model):
    _inherit = 'edi.message'
    
    @api.model
    def _clean_xml_dict(self, data):
        """
        Remove namespace prefixes and simplify XML dictionary structure.
        This is a flexible utility that can be used for any XML parsed by xmltodict.

        :param data: Dictionary from xmltodict.parse()
        :return: Cleaned dictionary without namespace prefixes
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Skip namespace declarations
                if key.startswith('@xmlns'):
                    continue

                # Remove namespace prefix from keys (cbc:ID -> ID)
                clean_key = key.split(':')[-1]

                # If value is a dict with only #text, unwrap it
                if isinstance(value, dict):
                    if len(value) == 1 and '#text' in value:
                        # Simple text node: {'#text': 'value'} -> 'value'
                        cleaned[clean_key] = value['#text']
                    elif '#text' in value and any(k.startswith('@') for k in value.keys()):
                        # Has both text and attributes, keep structure but clean
                        cleaned[clean_key] = {
                            'value': value['#text'],
                            'attributes': {k.lstrip('@'): v for k, v in value.items() if k.startswith('@')}
                        }
                    else:
                        # Regular nested dict
                        cleaned[clean_key] = self._clean_xml_dict(value)
                elif isinstance(value, list):
                    # List of elements
                    cleaned[clean_key] = [self._clean_xml_dict(item) for item in value]
                else:
                    # Simple value (string, number, etc.)
                    cleaned[clean_key] = value

            return cleaned
        elif isinstance(data, list):
            return [self._clean_xml_dict(item) for item in data]
        else:
            return data
            
    def _parse_payload_to_dict(self):
        """
        Parse binary XML payload to cleaned dictionary.
        Works for any UBL document type.

        :return: Cleaned dictionary or False
        """
        if not self.payload:
            _logger.warning("No payload to parse")
            return False

        try:
            # Decode the binary payload
            binary_data = base64.b64decode(self.payload)
            xml_string = binary_data.decode('utf-8')

            # Parse XML to dictionary
            raw_data = xmltodict.parse(xml_string)

            # Get the root element (try common UBL document types)
            document_types = [
                'Catalogue', 'ApplicationResponse', 'Invoice',
                'Order', 'OrderResponse', 'DespatchAdvice',
                'CreditNote', 'DebitNote'
            ]

            document = None
            for doc_type in document_types:
                document = raw_data.get(doc_type) or raw_data.get(f'ubl:{doc_type}')
                if document:
                    break

            if not document:
                _logger.error(f"No recognized UBL document found in XML. Root keys: {raw_data.keys()}")
                return False

            # Clean the dictionary
            cleaned_data = self._clean_xml_dict(document)

            _logger.info(f"Parsed document type with ID: {cleaned_data.get('ID')}")

            return cleaned_data

        except Exception as e:
            _logger.error(f"Error parsing payload: {e}")
            return False
    
    def _set_message_type(self, payload_dict):
        """
        Set message format based on CustomizationID.

        :param payload_dict: Parsed payload dictionary
        """
        if not payload_dict:
            return

        customization_id = payload_dict.get('CustomizationID')

        if not customization_id:
            _logger.warning("No CustomizationID found in payload")
            return

        edi_message_format = self.env['edi.message.format'].search([
            ('name', '=', customization_id)
        ], limit=1)

        if edi_message_format:
            self.message_format_id = edi_message_format
            _logger.info(f"Set message format: {customization_id}")
        else:
            _logger.warning(f"No message format found for CustomizationID: {customization_id}")


    def _set_receiver_sender(self, payload_dict):
        """
        Extract and set sender and receiver from payload dictionary.
        Works with different UBL document party naming conventions.

        :param payload_dict: Parsed payload dictionary
        """
        if not payload_dict:
            return

        # Handle different party naming conventions across UBL documents
        # Catalogue: ProviderParty/ReceiverParty
        # ApplicationResponse: SenderParty/ReceiverParty
        # Invoice: AccountingSupplierParty/AccountingCustomerParty
        # Order: BuyerCustomerParty/SellerSupplierParty
        sender_party = (
                payload_dict.get('ProviderParty') or
                payload_dict.get('SenderParty') or
                payload_dict.get('AccountingSupplierParty') or
                payload_dict.get('SellerSupplierParty')
        )

        receiver_party = (
                payload_dict.get('ReceiverParty') or
                payload_dict.get('AccountingCustomerParty') or
                payload_dict.get('BuyerCustomerParty')
        )

        # Extract sender
        if sender_party:
            sender_company, sender_contact = self._extract_party(sender_party, 'sender')
            if sender_company:
                self.sender = sender_company

        # Extract receiver
        if receiver_party:
            receiver_company, receiver_contact = self._extract_party(receiver_party, 'receiver')
            if receiver_company:
                self.receiver = receiver_company

    def _parse_date(self, date_str, time_str=None):
        """
        Parse date and optional time to datetime/date object.

        :param date_str: Date string 'YYYY-MM-DD'
        :param time_str: Optional time string 'HH:MM:SS'
        :return: datetime/date object or False
        """
        if not date_str:
            return False

        try:
            if time_str:
                datetime_str = f"{date_str} {time_str.split('.')[0]}"  # Remove microseconds if present
                return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            _logger.warning(f"Invalid date/time format: {date_str} {time_str}")
            return False
