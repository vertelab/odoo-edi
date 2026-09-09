# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models

PAYEE_BANK_MODE_SELECTION = [
    ('auto', 'Automatic (by currency)'),
    ('domestic', 'Bankgiro / Plusgiro (SEK)'),
    ('iban', 'IBAN / SEPA (foreign currency)'),
]

# IBAN: 2 letters + 2 check digits + up to 30 alphanumeric chars.
_IBAN_RE = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$')

# Swedish domestic account numbers (no letters):
# Bankgiro 7-8 digits, Plusgiro 5-7 digits.
_DOMESTIC_SE_RE = re.compile(r'^\d{5,8}$')


class AccountMove(models.Model):
    """Deterministic payee bank selection for Peppol invoices.

    Standard Odoo's ``_compute_partner_bank_id`` simply takes the first trusted
    bank account, without looking at the invoice currency. That means a Swedish
    company with both a Bankgiro/Plusgiro account and an IBAN can end up
    instructing a foreign-currency (EUR/USD...) customer to pay to a SEK-only
    Bankgiro — impossible to execute (and wrong in Peppol BIS3, BR-61).

    This module adds an explicit, visible on the invoice:

    * ``payee_bank_mode`` selection (auto / domestic / iban)
    * ``_pick_payee_bank`` chooses the account by currency (SEK -> Bankgiro,
      foreign -> IBAN) when mode is auto; the user can force domestic/iban.
    * Bankgiro/Plusgiro are treated as legacy: once NO domestic account exists
      any more (Bankgiro being phased out in Sweden), the code automatically
      falls back to IBAN even for SEK invoices.

    Detection is number-based (not acc_type) because standard Odoo never sets
    acc_type='iban'; Bankgiro/Plusgiro are also often stored as 'bank'.
    """

    _inherit = 'account.move'

    payee_bank_mode = fields.Selection(
        selection=PAYEE_BANK_MODE_SELECTION,
        string='Payee bank',
        default='auto',
        help="""
Automatic (by currency): SEK invoices use the domestic account (Bankgiro /
Plusgiro) when one exists; foreign-currency invoices use the IBAN account.
Bankgiro / Plusgiro (SEK): always use the domestic Swedish account.
IBAN / SEPA (foreign currency): always use the IBAN account.

If no matching account exists, the other type is used as a fallback.
""",
    )

    incoming_peppol_banks = fields.Json(
        string='Received bank accounts',
        help="""
Every bank account received on an incoming Peppol invoice, as a list of
{acc_type, acc_number, is_selected}. Populated at import time so the full
payment picture is visible on the vendor bill.
""",
    )

    incoming_peppol_banks_display = fields.Char(
        string='Received bank accounts',
        compute='_compute_incoming_peppol_banks_display',
        help="Readable summary of the bank accounts received on the invoice.",
    )

    @api.depends('incoming_peppol_banks')
    def _compute_incoming_peppol_banks_display(self):
        for move in self:
            banks = move.incoming_peppol_banks or []
            if not banks:
                move.incoming_peppol_banks_display = False
                continue
            parts = []
            for bank in banks:
                marker = ' (recipient)' if bank.get('is_selected') else ''
                parts.append('%s %s%s' % (bank.get('acc_type'), bank.get('acc_number'), marker))
            move.incoming_peppol_banks_display = ', '.join(parts)

    def _is_iban_account(self, bank):
        """True when the account number looks like an IBAN (SE35..., DE89...)."""
        self.ensure_one()
        return bool(bank.sanitized_acc_number and _IBAN_RE.match(bank.sanitized_acc_number))

    def _is_domestic_se_account(self, bank):
        """True for Bankgiro/Plusgiro (7-8/5-7 digits, no letters)."""
        self.ensure_one()
        # Bankgiro/Plusgiro may be stored with a dash or spaces; use sanitized.
        return bool(bank.sanitized_acc_number and _DOMESTIC_SE_RE.match(bank.sanitized_acc_number))

    def _get_payee_bank_accounts(self):
        """Return (domestic, international) bank accounts available for the move.

        Domestic = Bankgiro/Plusgiro (numeric, ≤8 digits); international =
        IBAN-looking account numbers. The caller's company partner is used.
        """
        self.ensure_one()
        company = self.company_id
        bank_partner = self.bank_partner_id
        bank_ids = bank_partner.bank_ids.filtered(
            lambda bank: (not bank.company_id or bank.company_id == company)
        )
        domestic = bank_ids.filtered(lambda bank: self._is_domestic_se_account(bank))
        international = bank_ids.filtered(lambda bank: self._is_iban_account(bank))
        return domestic, international

    def _pick_payee_bank(self, mode=None):
        """Choose the payee bank for the move based on the given mode.

        mode: 'auto' (default), 'domestic' or 'iban'. Falls back to the other
        type when the requested one does not exist.
        """
        self.ensure_one()
        domestic, international = self._get_payee_bank_accounts()
        mode = mode or self.payee_bank_mode or 'auto'
        if mode == 'domestic':
            return domestic[:1] or international[:1] or self.partner_bank_id
        if mode == 'iban':
            return international[:1] or domestic[:1] or self.partner_bank_id
        # auto
        foreign = self.currency_id != self.company_id.currency_id
        if foreign:
            return international[:1] or domestic[:1] or self.partner_bank_id
        return domestic[:1] or international[:1] or self.partner_bank_id

    @api.onchange('payee_bank_mode', 'currency_id', 'partner_id')
    def _onchange_payee_bank_mode(self):
        """Pick the payee bank according to the selected mode / currency."""
        for move in self:
            move.partner_bank_id = move._pick_payee_bank()

    @api.onchange('partner_bank_id')
    def _onchange_partner_bank_id(self):
        """When the user overrides the bank manually, reflect it in the mode."""
        for move in self:
            if not move.partner_bank_id:
                continue
            if move._is_domestic_se_account(move.partner_bank_id):
                move.payee_bank_mode = 'domestic'
            elif move._is_iban_account(move.partner_bank_id):
                move.payee_bank_mode = 'iban'

    @api.depends('currency_id', 'bank_partner_id', 'payee_bank_mode')
    def _compute_partner_bank_id(self):
        """EXTENDS account.move.

        For inbound documents (customer invoices, vendor credit notes) pick a
        bank account according to ``payee_bank_mode`` (by currency when auto).
        """
        super()._compute_partner_bank_id()
        for move in self:
            if not move.is_inbound():
                continue
            move.partner_bank_id = move._pick_payee_bank()