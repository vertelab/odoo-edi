# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiSession(models.Model):
    _name = 'edi.session'
    _description = 'Edi Session'

    sessions_line_ids = fields.One2many("edi.session.line", "session_id", string="Session Lines")
    route_id = fields.Many2one("edi.route", string="Route")
    reference = fields.Char(string="Reference")

