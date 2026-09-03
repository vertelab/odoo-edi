# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountEdiXmlUBLBIS3(models.AbstractModel):
    """Fix Peppol BIS3 payment instruction gaps.

    Two changes on top of Odoo's ``account_edi_ubl_cii``:

    * Keep the BIC / financial institution in ``PayeeFinancialAccount``
      (Odoo clears it for BIS3 by setting ``FinancialInstitution = None``).
    * Raise a blocking constraint when a Swedish domestic account type
      (Bankgiro / Plusgiro, exposed by ``l10n_se_bank``) is used on an
      invoice whose currency differs from the company currency.
    """

    _inherit = 'account.edi.xml.ubl_bis3'

    # ------------------------------------------------------------------
    # 1. Keep BIC / FinancialInstitution in BIS3 XML
    # ------------------------------------------------------------------

    def _ubl_get_payment_means_payee_financial_account_institution_branch_node_from_partner_bank(self, vals, partner_bank):
        """Override Odoo's BIS3 cleanup to keep BIC and bank info.

        Odoo (account_edi_xml_ubl_bis3.py) takes the base node and sets:

            node['cbc:ID']['schemeID'] = None
            node['cac:FinancialInstitution'] = None

        because the EN16931 BIS3 payload profile does not formally allow the
        full FinancialInstitution block. In practice, receivers (and their
        payment/banking systems) rely on the BIC to route the payment, so we
        rebuild the node exactly like the UBL base (account.edi.ubl) does,
        keeping the BIC schemeID and the FinancialInstitution block.
        """
        bank = partner_bank.bank_id
        if not bank:
            return None
        return {
            'cbc:ID': {
                '_text': bank.bic,
                'schemeID': 'BIC',
            },
            'cac:FinancialInstitution': {
                'cbc:ID': {
                    '_text': bank.bic,
                    'schemeID': 'BIC',
                },
                'cbc:Name': {'_text': bank.name},
                'cac:Address': self._ubl_get_partner_bank_address_node(vals, bank),
            },
        }

    # ------------------------------------------------------------------
    # 2. Block Bankgiro/Plusgiro on foreign-currency Peppol invoices
    # ------------------------------------------------------------------

    def _get_domestic_se_account_types(self):
        """Return the set of account types that are native-SEK-only.

        ``l10n_se_bank`` registers 'bankgiro' and 'plusgiro'. If that module
        is not installed, only 'bank' (normal) is available, which we do not
        block (a normal account may carry an IBAN in some setups).

        ``get_supported_account_types`` returns a list of (value, label)
        tuples, so we map to the first element.
        """
        supported = {
            value
            for value, _label in self.env['res.partner.bank'].get_supported_account_types()
        }
        return supported & {'bankgiro', 'plusgiro'}

    def _is_domestic_se_account(self, bank):
        """True when the account looks like a Bankgiro/Plusgiro number.

        Number-based (5-8 digits, no letters) and independent of acc_type,
        which standard Odoo never sets to 'iban' and only l10n_se_bank sets
        to 'bankgiro'/'plusgiro'.
        """
        import re
        return bool(bank.sanitized_acc_number and re.match(r'^\d{5,8}$', bank.sanitized_acc_number))

    def _is_iban_account(self, bank):
        """True when the account number looks like an IBAN."""
        import re
        return bool(bank.sanitized_acc_number and re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$', bank.sanitized_acc_number))

    def _invoice_constraints_peppol_en16931_ubl_new(self, invoice, vals):
        # EXTENDS account.edi.xml.ubl_bis3
        constraints = super()._invoice_constraints_peppol_en16931_ubl_new(invoice, vals)

        partner_bank = invoice.partner_bank_id
        if not partner_bank:
            return constraints

        invoice_currency = invoice.currency_id
        company_currency = invoice.company_id.currency_id
        if invoice_currency == company_currency:
            return constraints

        if not self._is_domestic_se_account(partner_bank):
            # IBAN or other non-domestic account: fine.
            return constraints

        # A Swedish domestic account (Bankgiro/Plusgiro) can only be paid in SEK.
        constraints['vertel_peppol_bankgiro_foreign_currency'] = _(
            "The payee bank account %(bank)s (%(acc_number)s) is a domestic Swedish "
            "account that can only be paid in SEK, but this invoice is in %(currency)s. "
            "Use an IBAN account (SEPA) for foreign-currency invoices, remove the bank "
            "account from the invoice, or invoice in SEK.",
            bank=partner_bank.display_name,
            acc_number=partner_bank.sanitized_acc_number,
            currency=invoice_currency.name,
        )
        return constraints