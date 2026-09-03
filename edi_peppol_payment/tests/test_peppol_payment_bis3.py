# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account_edi_ubl_cii.tests.common import TestUblBis3Common


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestPeppolPaymentBis3(TestUblBis3Common):
    """Verify the fixes delivered by edi_peppol_payment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The common mixin's test company uses EUR (currency_id=base.EUR). A
        # foreign-currency invoice therefore uses USD.
        cls.usd = cls.env.ref('base.USD')
        # 8 digits = Bankgiro; the company has both a Bankgiro and an IBAN.
        cls.bankgiro_number = '12345678'
        cls.iban_number = 'SE3550000000054910000003'
        cls._test_bic = 'TESTSEBB'

    def _create_bank(self, acc_number, acc_type='bank'):
        """Create a payee bank account on the company partner."""
        bank = self.env['res.bank'].create({
            'name': 'Testbank',
            'bic': self._test_bic,
        })
        return self.env['res.partner.bank'].create({
            'acc_number': acc_number,
            'acc_type': acc_type,
            'partner_id': self.env.company.partner_id.id,
            'allow_out_payment': True,
            'bank_id': bank.id,
        })

    def _create_invoice(self, currency=None, bank=None):
        tax = self.percent_tax(25.0)
        product = self._create_product(lst_price=100.0, taxes_id=tax)
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_be.id,
            'invoice_line_ids': [Command.create({
                'product_id': product.id,
                'price_unit': 100.0,
                'tax_ids': [Command.set(tax.ids)],
            })],
        }
        if bank:
            invoice_vals['partner_bank_id'] = bank.id
        if currency:
            invoice_vals['currency_id'] = currency.id
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        # `_compute_partner_bank_id` resolves via bank_partner_id (the customer
        # for out_invoice); mirror production where the user picks the payee
        # bank explicitly.
        if bank:
            invoice.partner_bank_id = bank
        return invoice

    def _company_with_both_accounts(self):
        """Give the company a Bankgiro + an IBAN account, return both."""
        bg = self._create_bank(self.bankgiro_number)
        iban = self._create_bank(self.iban_number)
        partner = self.env.company.partner_id
        partner.bank_ids = [Command.set((bg + iban).ids)]
        return bg, iban

    # ------------------------------------------------------------------
    # 1. BIC kept in BIS3
    # ------------------------------------------------------------------

    def test_bic_kept_in_bis3(self):
        """The BIC/FinancialInstitution must survive BIS3 export."""
        bank = self._create_bank(self.bankgiro_number)
        invoice = self._create_invoice(bank=bank)
        builder = self.env['account.edi.xml.ubl_bis3']
        xml_content, _errors = builder._export_invoice_new(invoice)

        tree = etree.fromstring(xml_content)
        ns = {
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        }
        pfa = tree.find('.//cac:PaymentMeans/cac:PayeeFinancialAccount', ns)
        self.assertTrue(pfa is not None, 'PayeeFinancialAccount should exist')

        branch = pfa.find('cac:FinancialInstitutionBranch', ns)
        self.assertTrue(branch is not None, 'FinancialInstitutionBranch should be kept')
        bic_id = branch.find('cbc:ID', ns)
        self.assertTrue(bic_id is not None and bic_id.text == self._test_bic,
                        'BIC should be present and correct')
        self.assertEqual(bic_id.get('schemeID'), 'BIC', 'schemeID=BIC should be kept')

        # FinancialInstitution lives UNDER the branch.
        fi = branch.find('cac:FinancialInstitution', ns)
        self.assertTrue(fi is not None, 'FinancialInstitution (bank name/BIC) should be kept')
        self.assertEqual(fi.find('cbc:Name', ns).text, 'Testbank')

    # ------------------------------------------------------------------
    # 2. Selection logic
    # ------------------------------------------------------------------

    def test_auto_selects_iban_for_foreign_currency(self):
        """With both accounts, auto mode must pick IBAN for foreign currency."""
        _bg, iban = self._company_with_both_accounts()
        invoice = self._create_invoice(currency=self.usd)
        invoice.bank_partner_id = self.env.company.partner_id
        invoice.payee_bank_mode = 'auto'
        self.assertEqual(invoice.partner_bank_id, iban,
                         'Auto mode on foreign-currency invoice should select IBAN')

    def test_auto_selects_domestic_for_company_currency(self):
        """With both accounts, auto mode must pick Bankgiro for EUR (company)."""
        bg, _iban = self._company_with_both_accounts()
        invoice = self._create_invoice()  # company currency (EUR)
        invoice.bank_partner_id = self.env.company.partner_id
        invoice.payee_bank_mode = 'auto'
        self.assertEqual(invoice.partner_bank_id, bg,
                         'Auto mode on company-currency invoice should select Bankgiro')

    def test_fallback_to_iban_when_no_domestic(self):
        """Without Bankgiro (phased out), auto falls back to IBAN."""
        iban = self._create_bank(self.iban_number)
        self.env.company.partner_id.bank_ids = [Command.set(iban.ids)]
        invoice = self._create_invoice(currency=self.usd)
        invoice.bank_partner_id = self.env.company.partner_id
        invoice.payee_bank_mode = 'auto'
        self.assertEqual(invoice.partner_bank_id, iban,
                         'Auto mode without domestic account should fall back to IBAN')

    def test_force_domestic_on_foreign_currency(self):
        """Explicit 'domestic' mode must use Bankgiro even on USD invoice."""
        bg, _iban = self._company_with_both_accounts()
        invoice = self._create_invoice(currency=self.usd)
        invoice.bank_partner_id = self.env.company.partner_id
        invoice.payee_bank_mode = 'domestic'
        self.assertEqual(invoice.partner_bank_id, bg,
                         'Force domestic should select Bankgiro on USD invoice')

    # ------------------------------------------------------------------
    # 3. Bankgiro + foreign currency blocked
    # ------------------------------------------------------------------

    def test_bankgiro_foreign_currency_blocked(self):
        """Bankgiro + foreign currency must raise a blocking constraint."""
        bg = self._create_bank(self.bankgiro_number)
        invoice = self._create_invoice(currency=self.usd, bank=bg)
        invoice.bank_partner_id = self.env.company.partner_id
        invoice.payee_bank_mode = 'domestic'
        invoice.partner_bank_id = bg
        _xml, errors = self.env['account.edi.xml.ubl_bis3']._export_invoice_new(invoice)

        self.assertTrue(
            any('bankgiro' in str(e).lower() or 'sepa' in str(e).lower() for e in errors),
            'Expected blocking constraint for Bankgiro + USD, got %s' % errors,
        )

    def test_iban_foreign_currency_allowed(self):
        """IBAN + foreign currency must NOT raise the constraint."""
        iban = self._create_bank(self.iban_number)
        invoice = self._create_invoice(currency=self.usd, bank=iban)
        invoice.bank_partner_id = self.env.company.partner_id
        invoice.payee_bank_mode = 'iban'
        invoice.partner_bank_id = iban
        _xml, errors = self.env['account.edi.xml.ubl_bis3']._export_invoice_new(invoice)

        self.assertFalse(
            any('bankgiro' in str(e) for e in errors),
            'IBAN + USD should not trigger the Bankgiro constraint, got %s' % errors,
        )