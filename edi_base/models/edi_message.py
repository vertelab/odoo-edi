# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiMessage(models.Model):
    _name = 'edi.message'
    _description = 'Edi Message'

    name = fields.Char(string="Name")
    message_format_id = fields.Many2one("edi.message.format", string="Message Format", ondelete="cascade")
    payload = fields.Binary(string="Payload")
    payload_filename = fields.Char(string="Payload filename")
    consignor = fields.Many2one("res.partner", string="Consignor")
    consignee = fields.Many2one("res.partner", string="Consignee")
    sender = fields.Many2one("res.partner", string="Sender")
    reciever = fields.Many2one("res.partner", string="Reciever")
    envelope_id = fields.Many2one("edi.envelope", string="Envelope")

    def pack(self):
        pass

    def unpack(self):
        pass

    