# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiMessage(models.Model):
    _name = 'edi.message'
    _description = 'Edi Message'

    message_format_id = fields.Many2one("edi.message.format", string="Message Format")
    payload = fields.Binary(string="Payload")
    consignor = fields.Many2one("res.contact", string="Consignor")
    consignee = fields.Many2one("res.contact", string="Consignee")
    sender = fields.Many2one("res.contact", string="Sender")
    reciever = fields.Many2one("res.contact", string="Reciever")
    envelope_id = fields.Many2one("edi.envelope", string="Envelope")
    company_id = fields.Many2one("res.company", string="Company")   

    def pack(self):
        pass

    def unpack(self):
        pass

    