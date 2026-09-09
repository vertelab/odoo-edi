# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

_INCOMING_BANK_PRIORITY_SELECTION = [
    ('default', 'Default (by country)'),
    ('bankgiro', 'Bankgiro'),
    ('plusgiro', 'Plusgiro'),
    ('iban', 'IBAN / SEPA'),
]


class ResPartner(models.Model):
    """Per-partner override for the incoming Peppol recipient-bank choice."""

    _inherit = 'res.partner'

    incoming_bank_priority = fields.Selection(
        selection=_INCOMING_BANK_PRIORITY_SELECTION,
        string='Incoming bank priority',
        default='default',
        help="""
Preferred recipient bank when an incoming Peppol invoice carries several
bank accounts. 'Default (by country)' uses the system parameter
(edi_incoming_bank_priority): Bankgiro for Swedish suppliers, otherwise IBAN.
Pick a specific type here to force it for this supplier.
""",
    )
