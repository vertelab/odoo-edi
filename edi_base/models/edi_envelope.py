# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiEnvelope(models.Model):
    _name = 'edi.envelope'
    _description = 'Edi Envelope'

    message_ids = fields.One2many("edi.message", "envelope_id", string="Messages")
    sender = fields.Many2one("res.partner", string="Sender")
    reciever = fields.Many2one("res.partner", string="Reciever")
    company_id = fields.Many2one("res.company", string="Company")

    def fold(self):
        pass

    def unfold(self):
        pass