from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class EdiMessageCatalogue(models.Model):
    _inherit = 'edi.message'

    catalogue_id = fields.Many2one('product.catalogue.peppol', string="Catalogue", readonly=True)

    def _process_peppol_message(self, payload):
        if self.message_format_id.name == "urn:fdc:peppol.eu:poacc:trns:catalogue:3":
            return self._unpack_catalogue(payload)
        return super()._process_peppol_message(payload)

    def _unpack_catalogue(self, payload):
        """Unpack PEPPOL Catalogue from payload"""
        party_mapping = {
            'ProviderParty': 'provider_party',
            'ReceiverParty': 'receiver_party',
            'SellerSupplierParty': 'seller_supplier_party',
            'ContractorCustomerParty': 'contractor_customer_party'
        }

        parties = self._get_parties(payload, party_mapping)

        catalogue_vals = {
            'name': payload.get('Name', 'Catalogue'),
            'edi_message_id': self.id
        }

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

                # Store legal entity in catalogue_vals
                catalogue_vals[party_key] = party_identification_partner.id

                if legal_entity_partner:
                    legal_entity_field_name = party_key.replace('_party', '_party_legal_entity')
                    catalogue_vals[legal_entity_field_name] = legal_entity_partner.id

                # ========== CREATE CONTACTS ==========
                if legal_entity_contacts:
                    for contact_data in legal_entity_contacts:
                        contact_type = contact_data.pop('type')

                        if contact_data.get('country_code'):
                            contact_data['country_id'] = self._get_country(contact_data.pop('country_code'))

                        if contact_type == 'postal':
                            # Postal address contact
                            contact_data['type'] = 'delivery'
                            contact_data['parent_id'] = legal_entity_partner.id
                            contact_address_field_name = party_key.replace('_party', '_postal_address')
                            catalogue_vals[contact_address_field_name] = self._find_or_create_partner(contact_data).id

                        elif contact_type == 'contact':
                            # Contact person
                            contact_data['type'] = 'contact'
                            contact_data['parent_id'] = legal_entity_partner.id
                            contact_field_name = party_key.replace('_party', '_contact')
                            catalogue_vals[contact_field_name] = self._find_or_create_partner(contact_data).id

        validity_period = payload.get('ValidityPeriod', {})
        if validity_period:
            catalogue_vals['validity_period_start_date'] = self._parse_date(validity_period.get('StartDate'))
            catalogue_vals['validity_period_end_date'] = self._parse_date(validity_period.get('EndDate'))

        referenced_contract = payload.get('ReferencedContract', {})
        if referenced_contract:
            catalogue_vals['referenced_contract'] = referenced_contract.get('ID')
            catalogue_vals['agreement_id'] = self._get_contract(referenced_contract.get('ID')).id

        # Set sender/receiver for EDI message (use legal entity partners)
        if 'provider_party' in catalogue_vals:
            self.sender = self.env['res.partner'].browse(catalogue_vals['provider_party'])
        if 'receiver_party' in catalogue_vals:
            self.receiver = self.env['res.partner'].browse(catalogue_vals['receiver_party'])

        return self._create_catalogue(catalogue_vals, payload)

    def _create_catalogue(self, catalogue_vals, payload):

        if not self.catalogue_id:
            product_catalogue_id = self.env['product.catalogue.peppol'].create(catalogue_vals)
            self.catalogue_id = product_catalogue_id.id

            self.write({ "res_model": product_catalogue_id._name, "res_id": product_catalogue_id.id })

        catalogue_lines = payload.get('CatalogueLine')

        for catalogue_line in catalogue_lines:
            # information about the catalogue
            action_code = catalogue_line.get('ActionCode', False)
            content_unit_quantity_data = catalogue_line.get('ContentUnitQuantity', {})

            content_unit_quantity = content_unit_quantity_data.get('value', False)
            content_unit_quantity_attributes = content_unit_quantity_data.get('attributes', {})
            content_unit_quantity_unit_code = content_unit_quantity_attributes.get('unitCode', False)
            orderable_unit = catalogue_line.get('OrderableUnit', False)
            minimum_order_quantity_data = catalogue_line.get('MinimumOrderQuantity', {})
            minimum_order_quantity = minimum_order_quantity_data.get('value', False)

            minimum_order_quantity_attribute = minimum_order_quantity_data.get('attributes', {})
            minimum_order_quantity_unit_code = minimum_order_quantity_attribute.get('unitCode', False)

            required_item_location_quantity = catalogue_line.get('RequiredItemLocationQuantity', {})
            catalogue_price_data = self._get_price_details(
                required_item_location_quantity_data=required_item_location_quantity
            )

            # lead_time_measure = required_item_location_quantity.get('LeadTimeMeasure', {})
            # applicable_territory_address = required_item_location_quantity.get('ApplicableTerritoryAddress', {})

            # information about the catalogue line item
            catalogue_item_data = self._get_catalogue_item(item=catalogue_line.get('Item'))
            product_id = self._get_product(catalogue_item_data=catalogue_item_data)

            self.env['product.catalogue.peppol.line'].create({
                'name': catalogue_item_data.get('name', False),
                'action_code': action_code,
                'catalogue_id': self.catalogue_id.id,
                'product_id': product_id.id,
                'product_tmpl_id': product_id.product_tmpl_id.id,
                'content_unit_quantity': content_unit_quantity,
                'min_order_quantity': minimum_order_quantity,
                'min_order_quantity_unit_code': minimum_order_quantity_unit_code,
                'sellers_item_identification': catalogue_item_data.get('sellers_item_identification'),
                'manufacturers_item_identification': catalogue_item_data.get('manufacturers_item_identification'),
                'item_specification_document_ref': catalogue_item_data.get('item_specification_document_ref'),
                'standard_item_identification_code': catalogue_item_data.get('standard_item_identification_code'),
                'standard_item_identification': catalogue_item_data.get('standard_item_identification'),
                'json_data': catalogue_line
            })
        self.catalogue_id.product_data = catalogue_lines

    def _get_contract(self, referenced_contract):
        return self.env['agreement'].search([('code', '=', referenced_contract)], limit=1)