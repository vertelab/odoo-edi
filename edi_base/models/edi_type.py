# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiType(models.Model):
    _name = "edi.type"
    _description = "Represents a type of EDI"

    name = fields.Char(string='Name')
    route_ids = fields.One2many(comodel_name='edi.route', inverse_name='type_id', string='Routes')
