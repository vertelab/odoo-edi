from datetime import datetime

from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)

import base64
import xmltodict


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
                _logger.warning("No message type found peppol")
                return False
            # return payload_dict
            self._process_peppol_message(payload=payload_dict)

        return result

    def _process_peppol_message(self, payload):
        return payload
    
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

    def _find_or_create_partner(self, partner_vals, search_domain=None):
        """
        Find or create a partner based on values.

        :param partner_vals: Dictionary of partner values
        :param search_domain: Optional custom search domain, otherwise uses peppol fields
        :return: res.partner record
        """
        if not search_domain:
            # Check if this is a contact (has parent_id)
            if partner_vals.get('parent_id'):
                # For contacts, search by name and parent
                search_domain = [
                    ('name', '=', partner_vals.get('name')),
                    ('parent_id', '=', partner_vals.get('parent_id'))
                ]
            else:
                # For companies, search by PEPPOL identifiers
                peppol_eas = partner_vals.get('peppol_eas')
                peppol_endpoint = partner_vals.get('peppol_endpoint')

                # Only search by PEPPOL if both values exist
                if peppol_eas and peppol_endpoint:
                    search_domain = [
                        ('peppol_eas', '=', peppol_eas),
                        ('peppol_endpoint', '=', peppol_endpoint),
                        ('name', '=', partner_vals.get('name')),
                    ]
                    print(search_domain)
                else:
                    # Fallback to name search
                    search_domain = [('name', '=', partner_vals.get('name'))]

        partner = self.env['res.partner'].search(search_domain, limit=1)

        if not partner:
            _logger.info(f"Created partner: {partner_vals}")
            partner = self.env['res.partner'].create(partner_vals)
            self.env.cr.commit()


        return partner

    def _get_party(self, party_data, party_role='party'):
        """
        Get party information from dictionary WITHOUT creating partners.
        Returns dictionary with nested structure for endpoint, identification, and legal entity.

        Handles multiple party structures:
        1. Direct parties (ProviderParty, ReceiverParty) - with PartyLegalEntity
        2. Wrapped parties (SellerSupplierParty/Party, ContractorCustomerParty/Party) - with PartyName
        3. Parties with PostalAddress at party level or in PartyLegalEntity

        :param party_data: Dictionary containing party information
        :param party_role: Role description for logging ('provider_party', 'seller_supplier_party', etc.)
        :return: Dictionary with nested party data structure
        """
        if not party_data:
            _logger.warning(f"No {party_role} party data found")
            return False

        # Handle wrapped party structure (e.g., SellerSupplierParty/Party)
        if 'Party' in party_data:
            party_data = party_data['Party']

        # ========== LEVEL 1: ENDPOINT (Routing) ==========
        endpoint_id = party_data.get('EndpointID', {})
        endpoint_value = endpoint_id.get('value', False)
        endpoint_scheme = endpoint_id.get('attributes', {}).get('schemeID', False)

        # ========== LEVEL 2: PARTY IDENTIFICATION ==========
        party_identification = party_data.get('PartyIdentification', {})
        party_id = party_identification.get('ID', {})
        identification_code = party_id.get('value', False)
        identification_schema = party_id.get('attributes', {}).get('schemeID', False)

        # ========== LEVEL 3: LEGAL ENTITY ==========

        # Try PartyLegalEntity first (ProviderParty/ReceiverParty structure)
        party_legal_entity = party_data.get('PartyLegalEntity', {})
        registration_name = party_legal_entity.get('RegistrationName')

        # Fallback to PartyName (SellerSupplierParty/ContractorCustomerParty structure)
        if not registration_name:
            party_name = party_data.get('PartyName', {})
            registration_name = party_name.get('Name', False)

        # Extract CompanyID (only in PartyLegalEntity)
        company_id = party_legal_entity.get('CompanyID', {})
        company_registry = company_id.get('value', False)

        # Extract company address from RegistrationAddress (inside PartyLegalEntity)
        registration_address = party_legal_entity.get('RegistrationAddress')
        address_fields = {}
        if registration_address:
            country = registration_address.get('Country', {})
            address_fields = {
                'street': registration_address.get('StreetName', False),
                'street2': registration_address.get('AdditionalStreetName', False),
                'city': registration_address.get('CityName', False),
                'zip': registration_address.get('PostalZone', False),
                # 'state': registration_address.get('CountrySubentity', False),
                'country_code': country.get('IdentificationCode', False),
            }

        # ========== CONTACTS ==========
        contacts = []

        # Extract PostalAddress as a contact (at party level)
        postal_address = party_data.get('PostalAddress')
        if postal_address:
            country = postal_address.get('Country', {})
            contacts.append({
                'type': 'postal',
                'street': postal_address.get('StreetName', False),
                'street2': postal_address.get('AdditionalStreetName', False),
                'city': postal_address.get('CityName', False),
                'zip': postal_address.get('PostalZone', False),
                # 'state': postal_address.get('CountrySubentity', False),
                'country_code': country.get('IdentificationCode', False)
            })

        # Extract Contact person
        contact = party_data.get('Contact')
        if contact:
            contacts.append({
                'type': 'contact',
                'name': contact.get('Name') or contact.get('ID'),
                'ref': contact.get('ID'),
                'email': contact.get('ElectronicMail'),
                'phone': contact.get('Telephone'),
            })

        # ========== BUILD NESTED STRUCTURE ==========
        # Always use consistent naming: PartyIdentification and PartyLegalEntity
        result = {}

        # Level 1: Endpoint (routing)
        if endpoint_value and endpoint_scheme:
            result['peppol_eas'] = endpoint_scheme
            result['peppol_endpoint'] = endpoint_value

        # Level 2: PartyIdentification
        if identification_code and identification_schema:
            result['PartyIdentification'] = {
                'peppol_eas': identification_schema,
                'peppol_endpoint': identification_code,
            }

        # Level 3: PartyLegalEntity
        if registration_name or address_fields or contacts or company_registry:
            entity_data = {
                'name': registration_name,
                #'company_registry': company_registry,
                **address_fields,
                'contacts': contacts if contacts else False
            }
            result['PartyLegalEntity'] = entity_data

        _logger.info(f"Extracted {party_role}: {result.get('PartyLegalEntity', {}).get('name')}")
        return result if result else False

    def _get_parties(self, payload_dict, party_mapping):
        """
        Get MULTIPLE parties from payload WITHOUT creating partners.
        Returns dictionary of extracted data.

        :param payload_dict: Parsed payload dictionary
        :param party_mapping: Dictionary mapping party keys to their roles
                             Example: {
                                 'ProviderParty': 'provider',
                                 'ReceiverParty': 'receiver',
                                 'SellerSupplierParty': 'seller',
                                 'ContractorCustomerParty': 'contractor'
                             }
        :return: Dictionary of parties {role: {party_data}}
        """
        parties = {}

        for party_key, party_role in party_mapping.items():
            party_data = payload_dict.get(party_key)
            if party_data:
                extracted = self._get_party(party_data, party_role)
                if extracted:
                    parties[party_role] = extracted
                    _logger.info(f"Got {party_role}: {extracted.get('name')}")

        return parties

    def _get_country(self, country_code):
        if country_code:
            return self.env['res.country'].search([('code', '=', country_code)], limit=1).id
        return False


    def _get_catalogue_item(self, item):
        name = item.get('Name', False)
        description = item.get('Description', False)
        sellers_item_id = item.get('SellersItemIdentification', {}).get('ID', False)
        manufacturers_item_id = item.get('ManufacturersItemIdentification', {}).get('ID', False)
        standard_item_id = item.get('StandardItemIdentification', {}).get('ID', {})
        item_standard_document_ref = item.get('ItemSpecificationDocumentReference', {}).get('ID', False)
        standard_item_id_value = standard_item_id.get('value', False)
        standard_item_id_attributes_scheme_id = standard_item_id.get('attributes', {}).get('schemeID', False)

        # additional item property
        # additional_item_property_id = item.get('AdditionalItemProperty', {}).get('ID', {}) # this can be list sometimes
        # additional_item_property_name = item.get('AdditionalItemProperty', {}).get('Name')
        # additional_item_property_name = item.get('AdditionalItemProperty', {}).get('Value')

        return {
            'name': name,
            'description': description,
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
        # if not product_id:
        #     product_id = self.env['product.product'].create(catalogue_item_data)

        return product_id