# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
import base64
from datetime import datetime

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _inherit = "edi.message"

    def _pack(self):
        super(EdiMessage, self)._pack()

    def _unpack(self):
        return super(EdiMessage, self)._unpack()
