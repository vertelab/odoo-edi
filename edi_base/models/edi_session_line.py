# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiSessionLine(models.Model):
    _name = 'edi.session.line'
    _description = 'Edi Session Line'

    message_format_id = fields.Many2one("edi.message.format")
    transport_id = fields.Many2one("edi.transport", string="Transport")
    #domain = fields
    message_id = fields.Many2one("edi.message", string="Message")

    session_id = fields.Many2one("edi.session", string="Session")