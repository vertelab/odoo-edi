#This file is going to add the functions neeeded to fold/unfold envelope and pack/unpack messages.
from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)

import base64
import xml.etree.ElementTree as ET
import xmltodict
# xml_string is your XML content as a string


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

    # specification_type = fields.Char(string="Specification Type")
    
    def unpack(self):
        result = super().unpack()
        if not result:
            payload_dict = self._unpack_punch_out()
            self._set_message_type(payload_dict)
            if not self.message_format_id:
                return False
            self._set_receiver_sender(payload_dict)


    def _unpack_punch_out(self):
        """Unpack PEPPOL Punch Out Catalogue from payload"""
        if not self.payload:
            return

        try:
            # Decode the binary payload
            binary_data = base64.b64decode(self.payload)
            xml_string = binary_data.decode('utf-8')

            # Parse XML to dictionary
            raw_data = xmltodict.parse(xml_string)

            # Get the catalogue (handle with or without namespace prefix)
            response = raw_data.get('Catalogue') or raw_data.get('ubl:Catalogue')
            if not response:
                _logger.error("No Catalogue element found in XML")
                return

            # Clean the dictionary
            response_data = _clean_xml_dict(response)

            _logger.info(f"Unpacked catalogue: {response_data.get('ID')} with "
                         f"{len(response_data.get('CatalogueLine', []))} lines")

            return response_data

        except Exception as e:
            _logger.error(f"Error unpacking punch out catalogue: {e}")
            raise


    def _set_message_type(self, payload_dict):
        customization_id = payload_dict.get('CustomizationID')
        # Verify CustomizationID
        if customization_id != 'urn:fdc:peppol.eu:poacc:trns:punch_out:3':
            _logger.warning(f"Unexpected CustomizationID: {customization_id}")

        edi_message_type = self.env['edi.message.format'].search([('name', '=', customization_id)])
        self.message_format_id = edi_message_type

        if not edi_message_type:
            _logger.warning(f"Unexpected CustomizationID: {customization_id} No message type ")

    def _set_receiver_sender(self, payload_dict):
        ProviderParty = payload_dict.get("ProviderParty")

        PartyIdentification = ProviderParty.get("PartyIdentification")
        partyidentification = PartyIdentification.get('ID')
        provider_identification_code = partyidentification.get('value')
        provider_identification_schema = partyidentification.get('attributes').get('schemeID')

        print(provider_identification_code, provider_identification_schema)

        provider_identification_legal_name = ProviderParty.get("PartyLegalEntity")
        provider_identification_reg_name = provider_identification_legal_name.get("RegistrationName")
        print(provider_identification_reg_name)

        provider_company = self.env['res.partner'].search([
            ('peppol_eas', '=', provider_identification_schema),
            ('peppol_endpoint', '=', provider_identification_code)
        ])
        if not provider_company:
            provider_company = self.env['res.partner'].create({
                'peppol_eas': provider_identification_schema,
                'peppol_endpoint': provider_identification_code,
                'company_type': 'company',
                'name': provider_identification_reg_name,
            })
        self.sender = provider_company
        provider_contact = ProviderParty.get("Contact",False)
        if provider_contact:
            name = provider_contact.get('Name') if provider_contact.get('Name') else provider_contact.get('ID')
            ref = provider_contact.get('ID')
            mail = provider_contact.get('Telephone')
            phone = provider_contact.get('ElectronicMail')
            if name:
                provider_contact = self.env['res.partner'].search([
                    ('name', '=', name),
                    ('email', '=', mail),
                    ('phone', '=', phone),
                    ('parent_id','=',provider_company.id)
                ], limit=1)
                if not provider_contact:
                    provider_contact = self.env['res.partner'].create({
                        'name': name,
                        'email': mail,
                        'company_type': 'person',
                        'phone': phone,
                        'type': "contact",
                        'parent_id': provider_company.id,
                        'ref': ref,
                    })

        ReceiverParty = payload_dict.get("ReceiverParty")
        PartyIdentification = ReceiverParty.get("PartyIdentification")
        partyidentification = PartyIdentification.get('ID')
        provider_identification_code = partyidentification.get('value')
        provider_identification_schema = partyidentification.get('attributes').get('schemeID')

        receiver_company = self.env['res.partner'].search([
            ('peppol_eas', '=', provider_identification_schema),
            ('peppol_endpoint', '=', provider_identification_code)
        ])
        if not receiver_company:
            receiver_company = self.env['res.partner'].create({
                'peppol_eas': provider_identification_schema,
                'peppol_endpoint': provider_identification_code,
                'company_type': 'company',
                'name': provider_identification_reg_name,
            })


        self.receiver = receiver_company
        receiver_contact = ReceiverParty.get("Contact",False)
        if receiver_contact:
            print(receiver_contact)
            name = receiver_contact.get('Name') if receiver_contact.get('Name') else receiver_contact.get('ID')
            ref = receiver_contact.get('ID')
            mail = receiver_contact.get('Telephone')
            phone = receiver_contact.get('ElectronicMail')
            if name:
                receiver_contact = self.env['res.partner'].search([
                    ('name', '=', name),
                    ('email', '=', mail),
                    ('phone', '=', phone),
                    ('parent_id','=',receiver_company.id)
                ], limit=1)
                if not receiver_contact:
                    receiver_contact = self.env['res.partner'].create({
                        'name': name,
                        'email': mail,
                        'company_type': 'person',
                        'phone': phone,
                        'type':"contact",
                        'parent_id':receiver_company.id,
                        'ref':ref,
                    })







