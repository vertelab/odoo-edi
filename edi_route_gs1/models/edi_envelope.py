# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEnvelope(models.Model):
    _inherit = "edi.envelope"

    def fold(self):
        return super(EdiEnvelope, self).fold()

    def _fold(self):
        return super(EdiEnvelope, self)._fold()
