from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class EdiMessageCatalogue(models.Model):
    _inherit = 'edi.message'

    def _process_peppol_message(self, payload):
        if self.message_format_id.name == "urn:fdc:peppol.eu:poacc:trns:catalogue:3":
            return self._unpack_catalogue(payload)
        return super()._process_peppol_message(payload)


    def _unpack_catalogue(self, payload):
        """Unpack PEPPOL Punch Out Catalogue from payload"""
        party_mapping = {
            'ProviderParty': 'provider_party',
            'ReceiverParty': 'receiver_party',
            'SellerSupplierParty': 'seller_supplier_party',
            'ContractorCustomerParty': 'contractor_customer_party'
        }

        parties = self._get_parties(payload, party_mapping)

        catalogue_vals = {
            'name': payload.get('Name', 'Catalogue'),
        }

        for party in party_mapping.values():
            party_data = parties[party]
            party_contact_data = party_data.pop('contact', False)
            if party_data.get('country_code'):
                party_data['country_id'] = self._get_country(party_data.pop('country_code', False))

            if parent_partner_id := self._find_or_create_partner(party_data):
                catalogue_vals[party] = parent_partner_id.id

                if party_contact_data:
                    party_contact_data['type'] = 'contact'
                    party_contact_data['parent_id'] = parent_partner_id.id
                    contact_field_name = party.replace('_party', '_contact')
                    catalogue_vals[contact_field_name] = self._find_or_create_partner(party_contact_data).id

        validity_period = payload.get('ValidityPeriod', {})
        if validity_period:
            catalogue_vals['validity_period_start_date'] = self._parse_date(validity_period.get('StartDate'))
            catalogue_vals['validity_period_end_date'] = self._parse_date(validity_period.get('EndDate'))

        referenced_contract = payload.get('ReferencedContract', {})
        if referenced_contract:
            catalogue_vals['referenced_contract'] = referenced_contract.get('ID')

        # Set sender/receiver for EDI message
        if 'provider_party' in catalogue_vals:
            self.sender = self.env['res.partner'].browse(catalogue_vals['provider_party'])
        if 'receiver_party' in catalogue_vals:
            self.receiver = self.env['res.partner'].browse(catalogue_vals['receiver_party'])

        return self._create_catalogue(catalogue_vals)

    def _create_catalogue(self, catalogue_vals):
        self.env['product.catalogue.peppol'].create(catalogue_vals)