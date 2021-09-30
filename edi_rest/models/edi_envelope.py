# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEnvelopeRest(models.Model):
    _inherit = "edi.envelope"

    def get_headers(self):
        return {}

    # def send(self):
    #     for rec in self:
    #         if rec.route_id.protocol == "rest" and rec.route_id.rest_api == "":