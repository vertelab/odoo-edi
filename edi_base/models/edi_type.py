# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiType(models.Model):
    _name = "edi.type"
    _description = "Mixin into model to add support for REST"

    name = fields.Char(string='Name')
    route_id = fields.Many2one(comodel_name='edi.route', string='Route')
    protocol = fields.Selection(string='Protocols', selection=[])
