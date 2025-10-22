# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiEnvelope(models.Model):
    _name = 'edi.envelope'
    _description = 'Edi Envelope'

    name = fields.Char(string="Name")
    message_ids = fields.One2many("edi.message", "envelope_id", string="Messages")
    sender = fields.Many2one("res.partner", string="Sender")
    receiver = fields.Many2one("res.partner", string="Receiver")
    payload = fields.Binary(string="Payload")
    payload_filename = fields.Char(string="Payload Filename")
    type = fields.Selection(string="Type", selection=[('none', 'None')])
    state = fields.Selection(string="State", selection=[
        ('to_be_sent', 'To be sent'),('sent', 'Sent'), ('received', 'Received'), ('error', 'Error')])

    transport_id = fields.Many2one('edi.transport', string="Transport")

    def add_message(self, message_id):
        pass
    
    def fold(self):
        pass

    def split(self):
        pass

    def unfold(self):
        pass
