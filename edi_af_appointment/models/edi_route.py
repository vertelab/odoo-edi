# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
import base64
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class edi_envelope(models.Model):
    _inherit = 'edi.envelope' 
    
    route_type = fields.Selection(selection_add=[('edi_af_schedules', 'AF schedules'), ('edi_af_ace_wi', 'AF ACE WI')])

    @api.one
    def fold(self,route): # Folds messages in an envelope
        envelope = super(edi_envelope,self).fold(route)
        return envelope

    @api.one
    def _split(self):
        if self.route_type == 'edi_af_schedules':
            msg = self.env['edi.message'].create({
                'name': 'plain',
                'envelope_id': self.id,
                'body': self.body,
                'route_type': self.route_type,
                'sender': self.sender,
                'recipient': self.recipient,
            })
            msg.unpack()
        self.envelope_opened()

class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    route_type = fields.Selection(selection_add=[('edi_af_schedules', 'AF schedules'), ('edi_af_ace_wi', 'AF ACE WI')])

class edi_message(models.Model):
    _inherit='edi.message'

    route_type = fields.Selection(selection_add=[('edi_af_schedules', 'AF schedules'), ('edi_af_ace_wi', 'AF ACE WI')])

    @api.one
    def _af_wi_compute(self):
        for record in self:
            if record.model_record and record.model_record._name == 'edi.ace_workitem':
                record.af_wi_start = record.model_record.appointment_id.start
                record.af_wi_stop = record.model_record.appointment_id.stop
                record.af_wi_pnr = record.sudo().model_record.appointment_id.partner_id.company_registry
                record.af_wi_type = record.model_record.appointment_id.type_id
                if record.state == "sent":
                    record.af_wi_reqid = record.body.get('requestId')
                    record.af_wi_conid = record.body.get('contactId')
                    record.af_wi_mailuid = record.body.get('emailUid')

    af_wi_start = fields.Datetime(string='Start time', compute="_af_wi_compute")
    af_wi_stop = fields.Datetime(string='End time', compute="_af_wi_compute")
    af_wi_type = fields.Many2one(string='Meeting type', comodel_name="calendar.appointment.type", compute="_af_wi_compute")
    af_wi_pnr = fields.Char(string='Jobseeker', compute="_af_wi_compute")
    af_wi_reqid = fields.Char(string='Request id', compute="_af_wi_compute")
    af_wi_conid = fields.Char(string='Contact id', compute="_af_wi_compute")
    af_wi_mailuid = fields.Char(string='Email uid', compute="_af_wi_compute")
