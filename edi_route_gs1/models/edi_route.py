# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
# from .edi_error import EDIUnkownMessageError

_logger = logging.getLogger(__name__)


class EdiRoute(models.Model):
    _inherit = "edi.route"

    def _run_in(self):
        res = super(EdiRoute, self)._run_in()
        for envelope in self.envelope_ids:
            envelope.receive()
        return res

    def _run_out(self, envelopes):
        res = super(EdiRoute, self)._run_out(envelopes)
        return res
