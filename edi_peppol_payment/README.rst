.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================
EDI: Peppol Payment
==================

Corrects payee bank instructions in Peppol BIS 3.0 for Swedish customers:

* keeps **BIC / financial institution** in the generated UBL XML,
* **picks the right payee account by currency** (Bankgiro for SEK, IBAN for
  foreign currency) via an explicit selection field on the invoice,
* **blocks invalid combinations** (Bankgiro + foreign currency) when sending
  via Peppol.

Configuration
=============

1. Install the module (requires Odoo Enterprise ``account_peppol`` and
   ``account_edi_ubl_cii``). Install ``l10n_se_bank`` to enable Bankgiro /
   Plusgiro account-type detection.
2. On your **company partner**, register the payee bank accounts:
   * one or more **Bankgiro / Plusgiro** accounts (SEK-only), and
   * one or more **IBAN** account with its **BIC** (for foreign currency).
3. On customer invoices, leave **Payee bank mode** = *Automatic (by currency)*.

Usage
=====

The module adds a **Payee bank mode** selection on customer invoices /
vendor credit notes:

* ``Automatic (by currency)`` — SEK invoice uses Bankgiro (if present),
  foreign-currency invoice uses IBAN.
* ``Bankgiro / Plusgiro (SEK)`` — always use the domestic account.
* ``IBAN / SEPA (foreign currency)`` — always use the IBAN account.

If no account of the requested type exists, the module falls back to the other
type automatically — so companies that no longer have Bankgiro (which is being
phased out in Sweden) simply use IBAN for everything.

| Invoice currency | Payee account used                |
| ---------------- | --------------------------------- |
| SEK              | Bankgiro / Plusgiro (if exists)   |
| EUR, USD, ...    | IBAN / SEPA (with BIC)            |

Bankgiro + foreign currency raises a blocking error when sending via Peppol
(Bankgiro is SEK-only; a Peppol credit transfer requires an IBAN, BR-61).

Incoming Peppol invoices
========================

When a supplier sends an invoice over Peppol with several bank accounts
(typically Bankgiro + Plusgiro + IBAN), the module picks the recipient bank
deterministically and type-aware, instead of Odoo's non-deterministic choice:

* a Swedish supplier gets **Bankgiro** (then Plusgiro, then IBAN),
* a supplier outside Sweden gets **IBAN**.

The order is configurable via the system parameter
``edi_incoming_bank_priority`` (JSON, e.g.
``{"SE": ["bankgiro", "plusgiro", "iban"], "default": ["iban"]}``), and
can be overridden per supplier via the **Incoming bank priority** field on the
supplier partner form.

Every bank account received on the invoice is shown on the vendor bill
(**Received bank accounts**, type + number) with the chosen recipient marked.

The account type is read from the XML branch id
(``FinancialInstitutionBranch/ID``: ``SE:BANKGIRO`` / ``SE:PLUSGIRO`` / BIC)
and falls back to number analysis, so it does not depend on ``l10n_se_bank``.

Known issues / Roadmap
======================

* BIC is always kept; receivers that strictly validate against the EN16931
  payload may warn about the extra ``FinancialInstitution`` block. In practice
  this is what payment systems need to route the payment.
* Tested on Odoo 18.0 Enterprise.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/vertelab/odoo-edi/issues>`_.

Credits
=======

Authors
~~~~~~~

* Vertel AB

Maintainers
~~~~~~~~~~~

This module is maintained by Vertel AB.