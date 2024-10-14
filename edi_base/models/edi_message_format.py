# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiMessageFormat(models.Model):
    _name = 'edi.message.format'
    _description = 'Edi Message Format'

    name = fields.Char(string="Name")
    message_ids = fields.One2many("edi.message", "message_format_id", string="Messages")

    def pack(self):
        pass
    
    def unpack(self):
        pass
