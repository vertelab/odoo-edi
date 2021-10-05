# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEnvelopeRest(models.Model):
    _inherit = "edi.envelope"
