# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _name = "edi.message"
    _description = "A single message to be sent in an envelope"

    name = fields.Char(string="Name", required=True)
    edi_state = fields.Selection(
        [
            ("created", "Created"),
            ("processing", "Processing"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("done", "Done"),
            ("canceled", "Canceled"),
        ],
        default="created",
    )
    edi_route_id = fields.Many2one(
        comodel_name="edi.route", required=True, default="_route_default"
    )
    edi_envelope_id = fields.Many2one(comodel_name="edi.envelope", required=True)

    def _route_default(self):
        for rec in self:
            res = self.env["edi.route"].browse(self._context.get("default_route_id"))
            if res.exists():
                rec._route_default = res.id
