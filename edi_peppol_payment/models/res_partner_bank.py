# -*- coding: utf-8 -*-
# Copyright 2026 Vertel AB
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResPartnerBank(models.Model):
    """Expose a helper to detect domestic Swedish account types."""

    _inherit = 'res.partner.bank'

    def _is_domestic_se_payment_account(self):
        """True for Bankgiro/Plusgiro (SEK-only) account types."""
        self.ensure_one()
        supported = set(self.get_supported_account_types())
        return self.acc_type in supported & {'bankgiro', 'plusgiro'}