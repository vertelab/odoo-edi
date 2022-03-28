# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEnvelope(models.Model):
    _name = "edi.envelope"
    _description = (
        "An envelope represents a group of edi.messages to be sent through an edi.route"
    )

    name = fields.Char(string="Name", required=True)
    sender_id = fields.Many2one(comodel_name="res.partner", string="Interchange Sender")
    recipient_id = fields.Many2one(
        comodel_name="res.partner", string="Interchange Recipient"
    )
    ref = fields.Char("Reference")
    body = fields.Binary(string="Body")
    state = fields.Selection(
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
    message_ids = fields.One2many(
        comodel_name="edi.message", inverse_name="envelope_id", string="Messages"
    )
    protocol_id = fields.Many2one('edi.protocol', string="Protocol")
    log_count = fields.Integer(compute="_log_count", string="no. logs")

    def _route_default(self):
        for rec in self:
            res = self.env["edi.route"].browse(self._context.get("default_route_id"))
            if res.exists():
                rec._route_default = res.id

    route_id = fields.Many2one(
        comodel_name="edi.route", required=True, default=_route_default
    )

    def _log_count(self):
        for rec in self:
            rec.log_count = self.env["edi.log"].search_count(
                [("message_id.envelope_id", "=", rec.id)]
            )

    def send(self):
        """Send the envelope"""
        pass

    @api.model
    def recieve(self):
        """Check for new envelopes, create new if any are found and
        return them in a RecordSet"""
        res = self.env['edi.envelope']
        return res

    def fold(self):
        self._fold()

    def _fold(self):
        for message in self.message_ids:
            message.pack()
