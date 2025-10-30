import logging

from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class EdiMessagePunchOut(models.Model):
    _inherit = 'edi.message'

    def _process_peppol_message(self, payload):
        if self.message_format_id.name == "urn:fdc:peppol.eu:poacc:trns:punch_out:3":
            return self._unpack_punch_out(payload)
        return super()._process_peppol_message(payload)

    def _unpack_punch_out(self, payload_dict):
        """Unpack PEPPOL Punch Out from payload"""
        party_mapping = {
            'ProviderParty': 'provider_party',
            'ReceiverParty': 'receiver_party',
        }

        parties = self._get_parties(payload_dict, party_mapping)

        # Process parties
        for party_key in party_mapping.values():
            party_data = parties.get(party_key)
            if not party_data:
                continue

            # ========== CREATE PARTY IDENTIFICATION PARTNER ==========
            party_identification = party_data.get('PartyIdentification', {})

            if party_identification:
                party_id_vals = {
                    'peppol_eas': party_identification.get('peppol_eas'),
                    'peppol_endpoint': party_identification.get('peppol_endpoint'),
                    'name': f"{party_identification.get('peppol_eas')}:{party_identification.get('peppol_endpoint')}",
                    'company_type': 'company',
                }
                party_identification_partner = self._find_or_create_partner(party_id_vals)
            else:
                party_identification_partner = None

            # ========== CREATE PARTY LEGAL ENTITY PARTNER ==========
            party_legal_entity = party_data.get('PartyLegalEntity', {})

            if party_legal_entity:
                legal_entity_vals = party_legal_entity.copy()
                legal_entity_contacts = legal_entity_vals.pop('contacts', [])

                if legal_entity_vals.get('country_code'):
                    legal_entity_vals['country_id'] = self._get_country(legal_entity_vals.pop('country_code'))

                legal_entity_vals['company_type'] = 'company'

                # Link to PartyIdentification as parent
                if party_identification_partner:
                    legal_entity_vals['parent_id'] = party_identification_partner.id

                legal_entity_partner = self._find_or_create_partner(legal_entity_vals)

                # ========== CREATE CONTACTS ==========
                if legal_entity_contacts:
                    for contact_data in legal_entity_contacts:
                        contact_type = contact_data.pop('type')

                        if contact_data.get('country_code'):
                            contact_data['country_id'] = self._get_country(contact_data.pop('country_code'))

                        if contact_type == 'postal':
                            contact_data['type'] = 'delivery'
                            contact_data['parent_id'] = legal_entity_partner.id
                            self._find_or_create_partner(contact_data)

                        elif contact_type == 'contact' and contact_data.get('name'):
                            contact_data['type'] = 'contact'
                            contact_data['parent_id'] = legal_entity_partner.id
                            self._find_or_create_partner(contact_data)

                # ========== SET SENDER/RECEIVER ==========
                # Use the legal entity as the main partner for the transaction
                if party_key == 'provider_party':
                    self.sender = legal_entity_partner
                elif party_key == 'receiver_party':
                    self.receiver = legal_entity_partner

        if self.sender and self.receiver:
            return self._create_purchase_order(payload_dict)
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
            'partner_ref': payload_dict.get('ReferencedContract').get('ID', False) # todo: double check this is the right value
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
        
        self.write({"res_model":purchase_id._name, "res_id":purchase_id.id})
        return purchase_id

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

    # def _get_catalogue_item(self, item):
    #     sellers_item_id = item.get('SellersItemIdentification', {}).get('ID', False)
    #     manufacturers_item_id = item.get('ManufacturersItemIdentification', {}).get('ID', False)
    #     standard_item_id = item.get('StandardItemIdentification', {}).get('ID', {})
    #     item_standard_document_ref = item.get('ItemSpecificationDocumentReference', {}).get('ID', False)
    #     standard_item_id_value = standard_item_id.get('value', False)
    #     standard_item_id_attributes_scheme_id = standard_item_id.get('attributes', {}).get('schemeID', False)
    #
    #     # additional item property
    #     additional_item_property_id = item.get('AdditionalItemProperty', {}).get('ID', {})
    #     additional_item_property_name = item.get('AdditionalItemProperty', {}).get('Name')
    #     additional_item_property_name = item.get('AdditionalItemProperty', {}).get('Value')
    #
    #     return {
    #         'sellers_item_identification': sellers_item_id,
    #         'manufacturers_item_identification': manufacturers_item_id,
    #         'item_specification_document_ref': item_standard_document_ref,
    #         'standard_item_identification_code': standard_item_id_attributes_scheme_id,
    #         'standard_item_identification': standard_item_id_value,
    #     }


