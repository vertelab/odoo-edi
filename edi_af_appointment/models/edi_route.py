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
import json
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

    def _appointment_schedules(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = self.env["edi.message"]

        for comp_day in res:
            # assumes that there's only ever one competence
            type_id = (
                message.env["calendar.appointment.type"]
                .search([("ipf_id", "=", comp_day.get("competence").get("id"))])
                .id
            )
            for schedule in comp_day.get("schedules"):
                # Create messages from result
                schedule["type_id"] = type_id
                # Convert dict to tuple since a dict can't be encoded to bytes type
                body = tuple(sorted(schedule.items()))
                vals = {
                    "name": "Appointment schedule reply",
                    "body": body,
                    "edi_type": message.edi_type.id,
                    "route_type": message.route_type,
                }
                res_set |= message.env["edi.message"].create(vals)

        # unpack messages
        if res_set:
            res_set.unpack()

        message.model_record.inactivate()

    def _appointment_ace_wi(self, message, res):
        # Why does these not update?
        message.state = "received"
        message.envelope_id.state = "received"
        message.body = json.dumps(res)

        ace_wi = message.env["edi.ace_workitem"].search([("id", "=", message.res_id)])
        app = message.env["calendar.appointment"].search(
            [("id", "=", ace_wi.appointment_id.id)]
        )
        app.state = "done"

class edi_message(models.Model):
    _inherit='edi.message'

    route_type = fields.Selection(selection_add=[('edi_af_schedules', 'AF schedules'), ('edi_af_ace_wi', 'AF ACE WI')])

    @api.depends('state')
    def _af_wi_compute(self):
        for record in self:
            if record.model_record and record.model_record._name == 'edi.ace_workitem':
                record.af_wi_start = record.model_record.appointment_id.start
                record.af_wi_stop = record.model_record.appointment_id.stop
                record.af_wi_pnr = record.sudo().model_record.appointment_id.partner_id.social_sec_nr
                record.af_wi_type = record.model_record.appointment_id.type_id
                if record.state == "sent":
                    body = json.loads(record.body)
                    record.af_wi_reqid = body.get('requestId')
                    record.af_wi_conid = body.get('contactId')
                    record.af_wi_mailuid = body.get('emailUid')

    af_wi_start = fields.Datetime(string='Start time', compute="_af_wi_compute", store=True)
    af_wi_stop = fields.Datetime(string='End time', compute="_af_wi_compute", store=True)
    af_wi_type = fields.Many2one(string='Meeting type', comodel_name="calendar.appointment.type", compute="_af_wi_compute", store=True)
    af_wi_pnr = fields.Char(string='Jobseeker', compute="_af_wi_compute", store=True)
    af_wi_reqid = fields.Char(string='Request id', compute="_af_wi_compute", store=True)
    af_wi_conid = fields.Char(string='Contact id', compute="_af_wi_compute", store=True)
    af_wi_mailuid = fields.Char(string='Email uid', compute="_af_wi_compute", store=True)
