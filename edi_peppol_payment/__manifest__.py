# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'EDI: Peppol Payment',
    'version': '18.0.1.0.0',
    'summary': """
        Keep payment instruction (BIC/financial institution) in Peppol BIS3 XML
        and validate that domestic payment accounts (Bankgiro/Plusgiro) are only
        used with the account's/native currency.
    """,
    'description': """
EDI: Peppol Payment
===================

Fixes two gaps in Odoo's Peppol BIS 3.0 export (account_edi_ubl_cii):

1. **Keep BIC / financial institution**
   Odoo's BIS3 builder deliberately empties the
   ``cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch`` node
   (``node['cac:FinancialInstitution'] = None``) and removes the BIC schemeID.
   This module keeps that information so receivents can see the payment method
   and BIC.

2. **Warn/block Bankgiro payment in foreign currency**
   When the invoice currency differs from the company currency and the payee
   account is a domestic Swedish account type (Bankgiro/Plusgiro via
   ``l10n_se_bank``), sending a Peppol document with a SEPA "credit transfer"
   (PaymentMeansCode 30) plus a non-IBAN account is wrong on two levels:
   - Bankgiro can only be paid in SEK (and with an OCR reference in SEK).
   - A credit transfer (code 30) requires an IBAN (Peppol BR-61).
   This module raises a blocking error in that case, telling the user to either
   use an IBAN account, remove the bank account, or invoice in SEK.
    """,
    'category': 'Accounting/Accounting',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-',
    'license': 'AGPL-3',
    'depends': [
        'edi_base',
        'account_peppol',
    ],
    'data': [],
    'demo': [],
    'application': False,
    'installable': True,
    'auto_install': False,
}