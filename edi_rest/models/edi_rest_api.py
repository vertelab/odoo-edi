# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiRestApi(models.Model):
    _name = "edi.rest.api"
    _description = "A specific implementation of REST"

    name = fields.Char(string='Name')
