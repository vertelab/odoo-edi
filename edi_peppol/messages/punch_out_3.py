from datetime import datetime

from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)

import base64
import xml.etree.ElementTree as ET
import xmltodict


def _clean_xml_dict(data):
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
                    cleaned[clean_key] = _clean_xml_dict(value)
            elif isinstance(value, list):
                # List of elements
                cleaned[clean_key] = [_clean_xml_dict(item) for item in value]
            else:
                # Simple value (string, number, etc.)
                cleaned[clean_key] = value

        return cleaned
    elif isinstance(data, list):
        return [_clean_xml_dict(item) for item in data]
    else:
        return data


class EdiMessage(models.Model):
    _inherit = 'edi.message'

    def unpack(self):
        result = super().unpack()
        if not result:
            payload_dict = self._parse_payload_to_dict()
            if not payload_dict:
                return False

            self._set_message_type(payload_dict)
            if not self.message_format_id:
                return False

            self._set_receiver_sender(payload_dict)
            if self.sender and self.receiver:
                self._create_purchase_order(payload_dict)
            return payload_dict
        return result

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
            cleaned_data = _clean_xml_dict(document)

            _logger.info(f"Parsed document type with ID: {cleaned_data.get('ID')}")

            return cleaned_data

        except Exception as e:
            _logger.error(f"Error parsing payload: {e}")
            return False

    def _unpack_punch_out(self):
        """
        Legacy method - now just calls _parse_payload_to_dict.
        Kept for backward compatibility.
        """
        return self._parse_payload_to_dict()

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

    def _find_or_create_partner(self, partner_vals, search_domain=None):
        """
        Find or create a partner based on values.

        :param partner_vals: Dictionary of partner values
        :param search_domain: Optional custom search domain, otherwise uses peppol fields
        :return: res.partner record
        """
        if not search_domain:
            # Default search by PEPPOL identifiers
            peppol_eas = partner_vals.get('peppol_eas')
            peppol_endpoint = partner_vals.get('peppol_endpoint')

            # Only search by PEPPOL if both values exist
            if peppol_eas and peppol_endpoint:
                search_domain = [
                    ('peppol_eas', '=', peppol_eas),
                    ('peppol_endpoint', '=', peppol_endpoint)
                ]
            else:
                # Fallback to name search
                search_domain = [('name', '=', partner_vals.get('name'))]

        partner = self.env['res.partner'].search(search_domain, limit=1)

        if not partner:
            partner = self.env['res.partner'].create(partner_vals)
            _logger.info(f"Created partner: {partner_vals.get('name')}")

        return partner

    def _extract_party(self, party_data, party_role='party'):
        """
        Extract party information from dictionary.
        This is a reusable utility for any UBL document.

        :param party_data: Dictionary containing party information
        :param party_role: Role description for logging ('sender', 'receiver', 'supplier', etc.)
        :return: Tuple of (company_partner, contact_partner)
        """
        if not party_data:
            _logger.warning(f"No {party_role} party data found")
            return False, False

        # Extract party identification
        party_identification = party_data.get('PartyIdentification', {})
        party_id = party_identification.get('ID', {})

        identification_code = party_id.get('value') if isinstance(party_id, dict) else party_id
        identification_schema = party_id.get('attributes', {}).get('schemeID') if isinstance(party_id, dict) else None

        # Extract legal name
        party_legal_entity = party_data.get('PartyLegalEntity', {})
        registration_name = party_legal_entity.get('RegistrationName', f'{party_role.title()} Company')

        # Prepare company values
        company_vals = {
            'peppol_eas': identification_schema,
            'peppol_endpoint': identification_code,
            'company_type': 'company',
            'name': registration_name,
        }

        # Find or create company
        company = self._find_or_create_partner(company_vals)

        # Handle contact if present
        contact = False
        contact_data = party_data.get('Contact')

        if contact_data:
            contact_name = contact_data.get('Name') or contact_data.get('ID')
            contact_ref = contact_data.get('ID')
            contact_email = contact_data.get('ElectronicMail')
            contact_phone = contact_data.get('Telephone')

            if contact_name:
                contact_vals = {
                    'name': contact_name,
                    'email': contact_email,
                    'phone': contact_phone,
                    'company_type': 'person',
                    'type': 'contact',
                    'parent_id': company.id,
                    'ref': contact_ref,
                }

                # Search for existing contact by name and parent
                contact_search = [
                    ('name', '=', contact_name),
                    ('parent_id', '=', company.id)
                ]

                contact = self._find_or_create_partner(contact_vals, contact_search)

        return company, contact

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

    def _create_purchase_order(self, payload_dict):
        issue_date = self._parse_date(
            payload_dict.get('IssueDate'),
            payload_dict.get('IssueTime')
        )
        validity_period = self._parse_date(
            payload_dict.get('ValidityPeriod', {}).get('EndDate'),
            payload_dict.get('ValidityPeriod', {}).get('EndTime')
        )

        purchase_id = self.env['purchase.order'].create({
            'partner_id': self.sender.id,
            'issue_date': issue_date,
            'validity_period': validity_period,
        })

        catalogue_lines = payload_dict.get('CatalogueLine')

        for catalogue_line in catalogue_lines:
            # information about the catalogue
            required_item_location_quantity = catalogue_line.get('RequiredItemLocationQuantity', {})
            catalogue_price_data = self._get_price_details(
                required_item_location_quantity_data=required_item_location_quantity
            )

            # lead_time_measure = required_item_location_quantity.get('LeadTimeMeasure', {})
            # applicable_territory_address = required_item_location_quantity.get('ApplicableTerritoryAddress', {})

            # information about the catalogue line item
            catalogue_item_data = self._get_catalogue_item(item=catalogue_line.get('Item'))
            product_id = self._get_product(catalogue_item_data=catalogue_item_data)

            if product_id:
                self.env['purchase.order.line'].create({
                    'product_id': product_id.id,
                    "product_qty": catalogue_price_data.get('quantity'),
                    "price_unit": catalogue_price_data.get('price'),
                    'order_id': purchase_id.id
                })


    def _get_price_details(self, required_item_location_quantity_data):
        price = required_item_location_quantity_data.get('Price', {})

        price_amount = price.get('PriceAmount', {})
        price_amount_value = price_amount.get('value', False)
        price_amount_attributes = price_amount.get('attributes', {})
        price_amount_attributes_currency_id = price_amount_attributes.get('currencyID', False)

        base_quantity = price.get('BaseQuantity', {})
        base_quantity_value = base_quantity.get('value', False)
        base_quantity_attributes = base_quantity.get('attributes', {})
        base_quantity_attributes_unit_code = base_quantity_attributes.get('unitCode', False)

        return {
            'price': price_amount_value,
            'currency': price_amount_attributes_currency_id,
            'quantity': base_quantity_value,
            'uom': base_quantity_attributes_unit_code,
        }

    def _get_catalogue_item(self, item):
        sellers_item_id = item.get('SellersItemIdentification', {}).get('ID', False)
        manufacturers_item_id = item.get('ManufacturersItemIdentification', {}).get('ID', False)
        standard_item_id = item.get('StandardItemIdentification', {}).get('ID', {})
        item_standard_document_ref = item.get('ItemSpecificationDocumentReference', {}).get('ID', False)
        standard_item_id_value = standard_item_id.get('value', False)
        standard_item_id_attributes_scheme_id = standard_item_id.get('attributes', {}).get('schemeID', False)

        # additional item property
        additional_item_property_id = item.get('AdditionalItemProperty', {}).get('ID', {})
        additional_item_property_name = item.get('AdditionalItemProperty', {}).get('Name')
        additional_item_property_name = item.get('AdditionalItemProperty', {}).get('Value')

        return {
            'sellers_item_identification': sellers_item_id,
            'manufacturers_item_identification': manufacturers_item_id,
            'item_specification_document_ref': item_standard_document_ref,
            'standard_item_identification_code': standard_item_id_attributes_scheme_id,
            'standard_item_identification': standard_item_id_value,
        }

    def _get_product(self, catalogue_item_data):
        product_id = self.env['product.product'].search([
            ('sellers_item_identification', '=', catalogue_item_data.get('sellers_item_identification')),
            ('manufacturers_item_identification', '=', catalogue_item_data.get('manufacturers_item_identification')),
            ('standard_item_identification', '=', catalogue_item_data.get('standard_item_identification')),
        ], limit=1)
        return product_id