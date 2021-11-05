# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging


from odoo import api, fields, models, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import AccessError

logger = logging.getLogger(__name__)


class EDIMixin(models.AbstractModel):
    _name = 'edi.mixin'
    _description = 'EDI'

    edi_envelope_ids = fields.One2many(string="EDI Envelope")
    edi_message_ids = fields.One2many(string="EDI Message")

    def _edi_message_create(self, message_type):
        pass

    def edi_message_create(self, message_type):
        pass
