# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account_edi_ubl_cii.tests.common import TestUblBis3Common


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestPeppolPaymentBis3(TestUblBis3Common):
    """Verify the two fixes delivered by edi_peppol_payment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The common mixin's test company uses EUR (currency_id=base.EUR). A
        # foreign-currency invoice therefore uses USD.
        cls.usd = cls.env.ref('base.USD')
        cls._test_bank_number = '1234567890'
        cls._test_bic = 'TESTSEBB'

    def _create_bank(self, acc_type='bankgiro', acc_number=None, bic=None):
        acc_number = acc_number or self._test_bank_number
        bank = self.env['res.bank'].create({
            'name': 'Testbank',
            'bic': bic or self._test_bic,
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
        # `_compute_partner_bank_id` depends on bank_partner_id which resolves to
        # the customer for out_invoice, so it may clear our explicit bank at post.
        # In production the user picks the payee bank explicitly; re-set it after
        # post to mirror that and to exercise the constraint.
        if bank:
            invoice.partner_bank_id = bank
        return invoice

    def _patch_domestic_types(self):
        """Simulate l10n_se_bank account types on res.partner.bank.

        Odoo 18 models cannot be patched on the recordset; patch the Python
        class instead (unittest.mock.patch.object on type(recordset)).
        """
        bank_model = type(self.env['res.partner.bank'])
        test_bank_number = self._test_bank_number

        def fake_get_supported_account_types(self):
            return [('bank', 'Normal'), ('bankgiro', 'Bankgiro'), ('plusgiro', 'Plusgiro')]

        def fake_retrieve_acc_type(self, acc_number):
            return ('bankgiro' if acc_number == test_bank_number
                    else ('iban' if str(acc_number).startswith('SE') else 'bank'))

        patcher_supported = patch.object(bank_model, 'get_supported_account_types', fake_get_supported_account_types)
        patcher_retrieve = patch.object(bank_model, 'retrieve_acc_type', fake_retrieve_acc_type)
        patcher_supported.start()
        patcher_retrieve.start()
        self.addCleanup(patcher_supported.stop)
        self.addCleanup(patcher_retrieve.stop)

    def test_bic_kept_in_bis3(self):
        """The BIC/FinancialInstitution must survive BIS3 export."""
        bank = self._create_bank()
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

        # FinancialInstitution lives UNDER the branch, not as a direct child.
        fi = branch.find('cac:FinancialInstitution', ns)
        self.assertTrue(fi is not None, 'FinancialInstitution (bank name/BIC) should be kept')
        self.assertEqual(fi.find('cbc:Name', ns).text, 'Testbank')

    def test_bankgiro_foreign_currency_blocked(self):
        """Bankgiro + foreign currency must raise a blocking constraint."""
        self._patch_domestic_types()
        bank = self._create_bank(acc_type='bankgiro')
        invoice = self._create_invoice(currency=self.usd, bank=bank)
        self.assertTrue(
            invoice.partner_bank_id and invoice.partner_bank_id.acc_type == 'bankgiro',
            'Partner bank should be re-set after post for the constraint to fire',
        )
        self.assertTrue(
            invoice.currency_id != invoice.company_id.currency_id,
            'Invoice currency should differ from company currency',
        )
        _xml, errors = self.env['account.edi.xml.ubl_bis3']._export_invoice_new(invoice)

        self.assertTrue(
            any('vertel_peppol_bankgiro' in str(e) or 'bankgiro' in str(e).lower() for e in errors),
            'Expected blocking constraint for Bankgiro + USD, got %s' % errors,
        )

    def test_iban_foreign_currency_allowed(self):
        """IBAN + foreign currency must NOT raise the constraint."""
        self._patch_domestic_types()
        bank = self._create_bank(acc_type='iban', acc_number='SE3550000000054910000003')
        invoice = self._create_invoice(currency=self.usd, bank=bank)
        _xml, errors = self.env['account.edi.xml.ubl_bis3']._export_invoice_new(invoice)

        self.assertFalse(
            any('vertel_peppol_bankgiro' in str(e) for e in errors),
            'IBAN + USD should not trigger the Bankgiro constraint, got %s' % errors,
        )