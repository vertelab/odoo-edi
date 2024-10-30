# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class EdiRoute(models.Model):
    _name = 'edi.route'
    _description = 'Edi Route'

    _rec_name = "route_type"

    route_type = fields.Char(string="Route Type")
    route_line_ids = fields.One2many("edi.route.line", "route_id", string="Route Lines")
    session_ids = fields.One2many("edi.session", "route_id", string="Sessions")

    def create_edi_session(self):
        self.ensure_one()

        edi_session = self.env['edi.session'].create({
            'route_type':self.route_type,
            'route_id':self.id,
        })
        
        for edi_line in self.route_line_ids:
            self.env['edi.session.line'].create({
                'message_format_id':edi_line.message_format_id.id,
                'transport_id':edi_line.transport_id.id,
                'domain':edi_line.domain,
                'session_id':edi_session.id,
        })

        return edi_session



    