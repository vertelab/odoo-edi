# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiSession(models.Model):
    _name = 'edi.session'
    _description = 'Edi Session'

    name = fields.Char(string="Name")
    route_type = fields.Char(string="Route Type")
    sessions_line_ids = fields.One2many("edi.session.line", "session_id", string="Session Lines")
    route_id = fields.Many2one("edi.route", string="Route")
    

    def get_current_session_line_index(self):
        for index, record in enumerate(self.env['edi.session']):
            if record.message_id == False or record.message_id == False:
                return index
        return 0


