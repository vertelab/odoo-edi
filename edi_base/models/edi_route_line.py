# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiRouteLine(models.Model):
    _name = 'edi.route.line'
    _description = 'Edi Route Line'

    message_format_id = fields.Many2one("edi.message.format", string="Edi Messages Formats")
    route_id = fields.Many2one("edi.route", string="Route")
    # transport_id =
    # domain 