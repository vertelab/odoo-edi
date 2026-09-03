# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'EDI: Peppol Payment',
    'version': '18.0.1.1.0',
    'summary': """
        Correct payee bank instructions in Peppol BIS 3.0: keep BIC, pick the
        right account by currency (Bankgiro for SEK, IBAN for foreign currency),
        and block invalid combinations.
    """,
    'description': """
EDI: Peppol Payment
===================

Fixes three gaps in Odoo's Peppol BIS 3.0 export (account_edi_ubl_cii) for
Swedish customers.

1.  **Keep BIC / financial institution in the XML**
    Odoo's BIS3 builder deliberately empties the
    ``cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch`` node
    (``node['cac:FinancialInstitution'] = None``) and removes the BIC
    ``schemeID``. This module keeps that information so the receiver sees
    the payment method and the BIC of the payee bank.

2.  **Automatic payee bank selection by currency** (``payee_bank_mode``)
    Standard Odoo picks the first trusted bank account without looking at
    the invoice currency. This module adds an explicit selection field on the
    invoice ("Payee bank mode"):

    * ``Automatic (by currency)`` — the default. Invoice in company currency
      (SEK) uses the domestic account (Bankgiro / Plusgiro) when one exists;
      invoice in any foreign currency (EUR, USD, ...) uses the IBAN account.
    * ``Bankgiro / Plusgiro (SEK)`` — always use the domestic account.
    * ``IBAN / SEPA (foreign currency)`` — always use the IBAN account.

    If no account of the requested type exists, the module falls back to the
    other type automatically (so a company that no longer has Bankgiro —
    which is being phased out in Sweden — simply uses IBAN for everything).

3.  **Block invalid Bankgiro + foreign currency (Peppol)**
    If the payee account is a domestic Swedish account (Bankgiro/Plusgiro via
    ``l10n_se_bank``) and the invoice currency differs from the company
    currency, sending the document via Peppol would be wrong on two levels:

    * Bankgiro can only be paid in SEK (and with an OCR reference in SEK).
    * A "credit transfer" (``PaymentMeansCode`` 30) requires an IBAN
      (Peppol BR-61).

    The module raises a blocking error in that case, telling the user to use
    an IBAN account, remove the bank account, or invoice in SEK.

How to use
----------

1.  Install ``edi_peppol_payment`` (Enterprise modules ``account_peppol`` and
    ``account_edi_ubl_cii`` are required). For Bankgiro/Plusgiro detection,
    also install ``l10n_se_bank``.

2.  Register the payee bank accounts on your company partner:

    * one (or more) **Bankgiro / Plusgiro** accounts (SEK-only), and
    * one (or more) **IBAN** account with its **BIC** (for foreign currency).

3.  Create your customer invoice and leave "Payee bank mode" on
    *Automatic (by currency)* — the module picks the correct account:

    ======================  ============================================
    Invoice currency        Payee account used
    ======================  ============================================
    SEK (company currency)  Bankgiro / Plusgiro (if it exists)
    EUR, USD, ...           IBAN / SEPA (with BIC)
    ======================  ============================================

    If you need to force an account for a particular invoice, switch the
    selection field manually.

4.  Send the invoice via Peppol as usual ("Send & print" → Peppol). The
    generated UBL BIS 3.0 XML will contain the correct payee account and BIC.

Requirements & notes
--------------------

* ``account_peppol`` + ``account_edi_ubl_cii`` (Odoo Enterprise).
* ``l10n_se_bank`` (Vertel / OCA) is recommended so Bankgiro/Plusgiro
  account types are detected. Without it, only the IBAN path is active.
* The module is a safe addition for any company using Peppol: it only changes
  the payee bank resolution on invoices and adds a validation.
""",
    'category': 'Accounting/Accounting',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-',
    'license': 'AGPL-3',
    'depends': [
        'edi_base',
        'account_peppol',
    ],
    'data': [
        'views/account_move_views.xml',
    ],
    'demo': [],
    'application': False,
    'installable': True,
    'auto_install': False,
}