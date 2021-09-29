# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiTypeRest(models.Model):
    _inherit = "edi.type"

    protocol = fields.Selection(string='Protocols', selection=[('rest', 'REST')])
