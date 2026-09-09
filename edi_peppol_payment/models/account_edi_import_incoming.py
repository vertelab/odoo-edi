# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import re

from odoo import _, models
from odoo.exceptions import UserError
from odoo.addons.base.models.res_bank import sanitize_account_number

# IBAN: 2 letters + 2 check digits + up to 30 alphanumeric chars.
_IBAN_RE = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$')
# Swedish domestic (Bankgiro/Plusgiro): 5-8 digits, no letters.
_DOMESTIC_SE_RE = re.compile(r'^\d{5,8}$')

# XML branch ids (FinancialInstitutionBranch/ID) -> our account-type keys.
_BRANCH_TYPE_MAP = {
    'SE:BANKGIRO': 'bankgiro',
    'SE:PLUSGIRO': 'plusgiro',
}

# Default priority: country code -> ordered list of account types.
_DEFAULT_BANK_PRIORITY = {
    'SE': ['bankgiro', 'plusgiro', 'iban'],
    'default': ['iban'],
}

_SYSTEM_PARAM = 'edi_incoming_bank_priority'


class AccountEdiImportIncoming(models.AbstractModel):
    """Deterministic, configurable recipient-bank selection on incoming
    Peppol (UBL BIS3) invoices, plus surfacing all received bank accounts.

    Odoo's ``account_edi_ubl_cii`` import reads every
    ``PaymentMeans/PayeeFinancialAccount/ID`` into a Python ``set``, iterates
    it in non-deterministic order and sets ``partner_bank_id`` to the first
    one that happens to come out of the iteration — ignoring the account type
    (``FinancialInstitutionBranch/ID``: ``SE:BANKGIRO`` / ``SE:PLUSGIRO`` or a
    BIC) and the supplier's country. This module makes the choice
    deterministic and type-aware:

    * ``bankgiro`` for Swedish suppliers (then ``plusgiro``, then ``iban``),
    * ``iban`` for suppliers outside Sweden,

    configurable via a system parameter and a per-partner override. It also
    records every received bank account (type + number) on the invoice so the
    whole payment picture is visible.
    """

    _inherit = 'account.edi.xml.ubl_bis3'

    # ------------------------------------------------------------------
    # Helpers: account-type classification
    # ------------------------------------------------------------------

    def _incoming_bank_type_from_branch(self, branch_id):
        """Map a FinancialInstitutionBranch/ID to our account-type key.

        ``SE:BANKGIRO``/``SE:PLUSGIRO`` map to their types; anything else is
        treated as ``iban`` (a BIC in that position identifies an IBAN
        account). Returns None when there is no branch id.
        """
        if not branch_id:
            return None
        return _BRANCH_TYPE_MAP.get(branch_id.upper(), 'iban')

    def _incoming_bank_type_from_number(self, acc_number):
        """Classify an account number (fallback when no branch type).

        IBAN regex first, then Swedish domestic (Bankgiro / Plusgiro)
        patterns, otherwise ``bank``.
        """
        sanitized = (acc_number or '').replace(' ', '').replace('-', '').upper()
        if not sanitized:
            return 'bank'
        if _IBAN_RE.match(sanitized):
            return 'iban'
        if _DOMESTIC_SE_RE.match(sanitized):
            return 'bankgiro'
        return 'bank'

    def _incoming_bank_type(self, acc_number, branch_id=None):
        """Resolve the account type, preferring the XML branch id."""
        branch_type = self._incoming_bank_type_from_branch(branch_id)
        if branch_type:
            return branch_type
        return self._incoming_bank_type_from_number(acc_number)

    # ------------------------------------------------------------------
    # Configurable priority
    # ------------------------------------------------------------------

    def _incoming_bank_priority_map(self):
        """Return the configured country -> [type,...] priority map.

        Falls back to the default when the system parameter is unset or
        invalid. The map is merged over the default so partial configs work.
        """
        default = dict(_DEFAULT_BANK_PRIORITY)
        raw = self.env['ir.config_parameter'].get_param(_SYSTEM_PARAM, '')
        if not raw:
            return default
        try:
            configured = json.loads(raw)
            if isinstance(configured, dict):
                default.update(configured)
        except (ValueError, TypeError):
            pass
        return default

    def _incoming_partner_country_code(self, partner):
        """Country code (upper) of the supplier's commercial partner."""
        commercial = partner.commercial_partner_id or partner
        return (commercial.country_id.code or '').upper()

    def _incoming_partner_priority(self, partner):
        """Ordered list of types for the given partner.

        A per-partner override (``incoming_bank_priority``) wins over the
        country-based default from the system parameter.
        """
        override = partner.incoming_bank_priority
        priority_map = self._incoming_bank_priority_map()
        if override and override != 'default':
            return [override]
        country_code = self._incoming_partner_country_code(partner)
        return priority_map.get(country_code) or priority_map.get('default', ['iban'])

    # ------------------------------------------------------------------
    # Deterministic selection
    # ------------------------------------------------------------------

    def _select_incoming_partner_bank(self, partner_banks, partner, type_map=None):
        """Pick the winner among the partner's received bank accounts.

        ``partner_banks`` is a recordset of ``res.partner.bank`` (already
        found or created). ``type_map`` maps account number -> type resolved
        from the XML branch; when absent the type is inferred from the number.
        Returns the winning bank account (or an empty recordset).
        """
        type_map = type_map or {}
        priority = self._incoming_partner_priority(partner)
        rank = {acc_type: i for i, acc_type in enumerate(priority)}

        def type_of(bank):
            return type_map.get(
                bank.sanitized_acc_number,
                self._incoming_bank_type_from_number(bank.sanitized_acc_number),
            )

        def sort_key(bank):
            return (rank.get(type_of(bank), len(rank)), bank.id)

        if not partner_banks:
            return partner_banks
        winner_id = sorted(partner_banks, key=sort_key)[0].id
        return partner_banks.browse(winner_id)

    # ------------------------------------------------------------------
    # UBL (BIS3) import path
    # ------------------------------------------------------------------

    def _import_ubl_invoice_add_partner_bank_values(self, collected_values):
        """EXTENDS account.edi.ubl.

        Keep the account type (from ``FinancialInstitutionBranch/ID``) next to
        each account number so the deterministic selection can use it.
        """
        super()._import_ubl_invoice_add_partner_bank_values(collected_values)
        tree = collected_values['tree']
        partner_bank_values = collected_values['partner_bank_values']
        # {account_number: branch_type} for every PaymentMeans/PayeeFinancialAccount.
        type_map = {}
        for pfa in tree.findall('./{*}PaymentMeans/{*}PayeeFinancialAccount'):
            number_node = pfa.find('{*}ID')
            branch_node = pfa.find('{*}FinancialInstitutionBranch/{*}ID')
            if number_node is None or not number_node.text:
                continue
            type_map[sanitize_account_number(number_node.text)] = self._incoming_bank_type_from_branch(
                branch_node.text if branch_node is not None else None
            )
        partner_bank_values['bank_type_map'] = type_map

    def _incoming_import_partner(self, collected_values):
        """Resolve the supplier partner for an incoming import.

        The way the supplier is carried in ``collected_values`` differs across
        Odoo branches: Community nests it under ``customer_values.customer``
        while Enterprise stores it directly as ``customer``. Accept both so
        the deterministic selection works on CE and EE alike.
        """
        move_type = collected_values['invoice'].move_type
        if move_type in ('out_refund', 'in_invoice'):
            return (
                collected_values.get('customer_values', {}).get('customer')
                or collected_values.get('customer')
            )
        if move_type in ('out_invoice', 'in_refund'):
            return collected_values['company'].partner_id
        return None

    def _import_ubl_retrieve_partner_bank(self, collected_values):
        """EXTENDS account.edi.ubl.

        Pick ``partner_bank_id`` deterministically via
        ``_select_incoming_partner_bank`` instead of the first in a
        non-deterministic ``set`` iteration. Also record every received bank
        account on the invoice.
        """
        company = collected_values['company']
        partner = self._incoming_import_partner(collected_values)
        if not partner:
            return

        partner_bank_values = collected_values['partner_bank_values']
        account_numbers = partner_bank_values['account_numbers']
        type_map = partner_bank_values.get('bank_type_map', {})
        logs = collected_values['logs']
        partner_banks = self.env['res.partner.bank']
        for account_number in account_numbers:
            try:
                partner_banks += self.env['res.partner.bank']._find_or_create_bank_account(
                    account_number=account_number,
                    partner=partner,
                    company=company,
                )
            except UserError as e:
                logs.append(_("The bank account couldn't be fetched: %s", str(e)))

        partner_bank_values['partner_banks'] = partner_banks
        if partner_banks:
            winner = self._select_incoming_partner_bank(partner_banks, partner, type_map)
            collected_values['to_write']['partner_bank_id'] = winner.id
            self._record_incoming_banks(
                collected_values['invoice'], partner_banks, type_map, winner
            )

    def _record_incoming_banks(self, invoice, partner_banks, type_map, winner):
        """Store every received bank account (type + number) on the invoice.

        Used to surface the full payment picture on the vendor bill. The
        chosen account is flagged so the UI can mark it as recipient bank.
        """
        if not partner_banks:
            return
        records = []
        for bank in partner_banks:
            acc_number = bank.sanitized_acc_number
            records.append({
                'acc_type': type_map.get(acc_number, self._incoming_bank_type_from_number(acc_number)),
                'acc_number': acc_number,
                'is_selected': bool(winner and bank.id == winner.id),
            })
        invoice.incoming_peppol_banks = records
