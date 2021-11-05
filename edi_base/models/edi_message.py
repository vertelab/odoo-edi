# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _name = "edi.message"
    _description = "A single message to be sent in an envelope"

    name = fields.Char(string="Name", required=True)
    edi_body = fields.Binary(string='Body')  # maybe use ir.attachement instead?
    carrier_id = fields.Many2one('res.partner', string="Carrier")
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    consignor_id = fields.Many2one('res.partner', string="Consignor")
    edi_envelope_id = fields.Many2one(comodel_name="edi.envelope", required=True)
    forwarder_id = fields.Many2one('res.partner', string="Forwarder")
    edi_direction = fields.Selection([('in', 'In'), ('out', 'Out')], string="Direction")
    message_type_id = fields.Many2one('edi.message.type', string="Message Type")
    protocol_id = fields.Many2one('edi.protocol', string="Protocol")
    recipient_id = fields.Many2one('res.partner', string="Recipient")
    route_id = fields.Many2one(
        comodel_name="edi.route", required=True, default="_route_default"
    )
    sender_id = fields.Many2one('res.partner', string="Sender")

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

    def _route_default(self):
        for rec in self:
            res = self.env["edi.route"].browse(self._context.get("default_route_id"))
            if res.exists():
                rec._route_default = res.id

    def _pack(self):
        pass

    def pack(self):
        try:
            self._pack()
        except Exception as e:
            pass

    def _unpack(self):
        pass

    def unpack(self):
        try:
            self._unpack()
        except Exception as e:
            pass


class EdiMessageType(models.Model):
    _name = "edi.message.type"
    _description = "EDI message types"

    name = fields.Char(string="Name")
