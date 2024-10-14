# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiRoute(models.Model):
    _name = 'edi.route'
    _description = 'Edi Route'

    route_type = fields.Char(string="Route Type")
    edi_line_ids = fields.One2many("edi.route.line", "route_id", string="Edi Lines")
    edi_session_ids = fields.One2many("edi.session", "route_id", string="Edi Sessions")