# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.account_edi_ubl_cii.tests.common import TestUblBis3Common

# The payment accounts used by the real supplier invoice XML 30841
# (Vitec BidTheatre -> Berget AI AB).
_BANKGIRO = '1355684'
_PLUSGIRO = '21413372'
_IBAN = 'SE2595000099604221413372'


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestIncomingPeppolBank(TestUblBis3Common):
    """Verify deterministic, type-aware recipient-bank selection on incoming
    Peppol (UBL BIS3) invoices, plus surfacing of all received accounts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The import path runs on the bis3 model; exercise its helpers there.
        cls.importer = cls.env['account.edi.xml.ubl_bis3']

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _supplier(self, country_code):
        country = self.env.ref('base.%s' % country_code.lower())
        return self.env['res.partner'].create({
            'name': 'Supplier %s' % country_code,
            'country_id': country.id,
            'is_company': True,
        })

    def _bank(self, partner, acc_number, acc_type='bank'):
        """A bank account on the given partner with the given number."""
        bank = self.env['res.bank'].create({'name': 'Testbank', 'bic': 'TESTSEBB'})
        return self.env['res.partner.bank'].create({
            'acc_number': acc_number,
            'acc_type': acc_type,
            'partner_id': partner.id,
            'allow_out_payment': True,
            'bank_id': bank.id,
        })

    def _three_accounts(self, partner):
        """Bankgiro + Plusgiro + IBAN accounts on the partner (in that order)."""
        bg = self._bank(partner, _BANKGIRO)
        pg = self._bank(partner, _PLUSGIRO)
        iban = self._bank(partner, _IBAN)
        return bg + pg + iban

    # ------------------------------------------------------------------
    # 1. Account-type classification (task 2.1)
    # ------------------------------------------------------------------

    def test_classify_from_number(self):
        """Number analysis classifies the three real account numbers."""
        cls = self.importer
        self.assertEqual(cls._incoming_bank_type_from_number(_BANKGIRO), 'bankgiro')
        self.assertEqual(cls._incoming_bank_type_from_number(_PLUSGIRO), 'bankgiro')
        self.assertEqual(cls._incoming_bank_type_from_number(_IBAN), 'iban')

    def test_classify_from_branch(self):
        """The XML branch id drives the type when present."""
        cls = self.importer
        self.assertEqual(cls._incoming_bank_type(_BANKGIRO, 'SE:BANKGIRO'), 'bankgiro')
        self.assertEqual(cls._incoming_bank_type(_PLUSGIRO, 'SE:PLUSGIRO'), 'plusgiro')
        # A BIC in the branch position means an IBAN account.
        self.assertEqual(cls._incoming_bank_type(_IBAN, 'NDEASESS'), 'iban')

    # ------------------------------------------------------------------
    # 2. Deterministic selection (task 2.2)
    # ------------------------------------------------------------------

    def test_se_supplier_picks_bankgiro(self):
        """A Swedish supplier with BG+PG+IBAN must select Bankgiro."""
        supplier = self._supplier('SE')
        accounts = self._three_accounts(supplier)
        # Reverse the recordset order to prove selection is not order-dependent.
        winner = self.importer._select_incoming_partner_bank(
            accounts[::-1], supplier,
            type_map={
                _BANKGIRO: 'bankgiro',
                _PLUSGIRO: 'plusgiro',
                _IBAN: 'iban',
            },
        )
        self.assertEqual(winner.sanitized_acc_number, _BANKGIRO)

    def test_se_supplier_plusgiro_when_no_bankgiro(self):
        """Without Bankgiro, a Swedish supplier falls back to Plusgiro."""
        supplier = self._supplier('SE')
        pg = self._bank(supplier, _PLUSGIRO)
        iban = self._bank(supplier, _IBAN)
        winner = self.importer._select_incoming_partner_bank(
            pg + iban, supplier,
            type_map={_PLUSGIRO: 'plusgiro', _IBAN: 'iban'},
        )
        self.assertEqual(winner.sanitized_acc_number, _PLUSGIRO)

    def test_foreign_supplier_picks_iban(self):
        """A non-SE supplier must select IBAN even when BG is present."""
        supplier = self._supplier('BE')
        accounts = self._three_accounts(supplier)
        winner = self.importer._select_incoming_partner_bank(
            accounts, supplier,
            type_map={
                _BANKGIRO: 'bankgiro',
                _PLUSGIRO: 'plusgiro',
                _IBAN: 'iban',
            },
        )
        self.assertEqual(winner.sanitized_acc_number, _IBAN)

    def test_per_partner_override_wins(self):
        """A per-partner override (IBAN) must beat the country default."""
        supplier = self._supplier('SE')
        supplier.incoming_bank_priority = 'iban'
        accounts = self._three_accounts(supplier)
        winner = self.importer._select_incoming_partner_bank(
            accounts, supplier,
            type_map={
                _BANKGIRO: 'bankgiro',
                _PLUSGIRO: 'plusgiro',
                _IBAN: 'iban',
            },
        )
        self.assertEqual(winner.sanitized_acc_number, _IBAN)

    def test_configured_priority_followed(self):
        """A system-parameter override (Plusgiro before Bankgiro) is honoured."""
        supplier = self._supplier('SE')
        accounts = self._three_accounts(supplier)
        param = self.env['ir.config_parameter']
        param.set_param('edi_incoming_bank_priority', '{"SE": ["plusgiro", "bankgiro", "iban"]}')
        try:
            winner = self.importer._select_incoming_partner_bank(
                accounts, supplier,
                type_map={
                    _BANKGIRO: 'bankgiro',
                    _PLUSGIRO: 'plusgiro',
                    _IBAN: 'iban',
                },
            )
        finally:
            param.set_param('edi_incoming_bank_priority', False)
        self.assertEqual(winner.sanitized_acc_number, _PLUSGIRO)

    def test_deterministic_regardless_of_type_map_absence(self):
        """Without a type map, number analysis must still be deterministic."""
        supplier = self._supplier('SE')
        accounts = self._three_accounts(supplier)
        winner = self.importer._select_incoming_partner_bank(accounts, supplier)
        self.assertEqual(winner.sanitized_acc_number, _BANKGIRO)

    # ------------------------------------------------------------------
    # 3. All received accounts are surfaced (task 4.1)
    # ------------------------------------------------------------------

    def test_all_three_accounts_surfaced(self):
        """_record_incoming_banks stores all three accounts, flags the winner."""
        supplier = self._supplier('SE')
        accounts = self._three_accounts(supplier)
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': supplier.id,
            'journal_id': self.company_data['default_journal_purchase'].id,
        })
        winner = self.importer._select_incoming_partner_bank(
            accounts, supplier,
            type_map={
                _BANKGIRO: 'bankgiro',
                _PLUSGIRO: 'plusgiro',
                _IBAN: 'iban',
            },
        )
        self.importer._record_incoming_banks(invoice, accounts, {
            _BANKGIRO: 'bankgiro',
            _PLUSGIRO: 'plusgiro',
            _IBAN: 'iban',
        }, winner)

        numbers = {b['acc_number'] for b in invoice.incoming_peppol_banks}
        self.assertEqual(numbers, {_BANKGIRO, _PLUSGIRO, _IBAN},
                         'All three received accounts should be recorded')
        selected = [b for b in invoice.incoming_peppol_banks if b['is_selected']]
        self.assertEqual(len(selected), 1, 'Exactly one account should be selected')
        self.assertEqual(selected[0]['acc_number'], _BANKGIRO)

    # ------------------------------------------------------------------
    # 4. Supplier-partner resolution is version-agnostic (CE and EE)
    # ------------------------------------------------------------------

    def test_partner_resolved_from_ce_customer_values(self):
        """CE stores the supplier under collected_values['customer_values']."""
        supplier = self._supplier('SE')
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': supplier.id,
            'journal_id': self.company_data['default_journal_purchase'].id,
        })
        collected = {
            'company': self.company_data['company'],
            'invoice': invoice,
            'customer_values': {'customer': supplier},
        }
        partner = self.importer._incoming_import_partner(collected)
        self.assertEqual(partner, supplier)

    def test_partner_resolved_from_ee_direct_customer(self):
        """EE stores the supplier directly as collected_values['customer']."""
        supplier = self._supplier('SE')
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': supplier.id,
            'journal_id': self.company_data['default_journal_purchase'].id,
        })
        collected = {
            'company': self.company_data['company'],
            'invoice': invoice,
            'customer': supplier,  # EE structure: no 'customer_values'
        }
        partner = self.importer._incoming_import_partner(collected)
        self.assertEqual(partner, supplier)

    def test_partner_resolved_from_company_for_out_invoice(self):
        """Outgoing moves resolve the partner to the company itself."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.company_data['company'].partner_id.id,
            'journal_id': self.company_data['default_journal_sale'].id,
        })
        collected = {'company': self.company_data['company'], 'invoice': invoice}
        partner = self.importer._incoming_import_partner(collected)
        self.assertEqual(partner, self.company_data['company'].partner_id)
