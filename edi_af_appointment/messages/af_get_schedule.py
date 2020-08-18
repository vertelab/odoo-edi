# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
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
from datetime import datetime, timedelta
import json
import pytz
import ast

import logging
_logger = logging.getLogger(__name__)

LOCAL_TZ = 'Europe/Stockholm'

class edi_message(models.Model):
    _inherit='edi.message'
            
    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_appointment.appointment_schedules').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = dict(ast.literal_eval(self.body.decode("utf-8")))
            
            start_time = datetime.strptime(body.get('start_time'), "%Y-%m-%dT%H:%M:%SZ")
            stop_time = datetime.strptime(body.get('end_time'), "%Y-%m-%dT%H:%M:%SZ")

            # Integration gives us times in local (Europe/Stockholm) tz
            # Convert to UTC
            start_time_utc = pytz.timezone(LOCAL_TZ).localize(start_time).astimezone(pytz.utc)
            stop_time_utc = pytz.timezone(LOCAL_TZ).localize(stop_time).astimezone(pytz.utc)

            # schedules can exist every half hour from 09:00 to 16:00
            # check if calendar.schedule already exists 
            type_id = self.env['calendar.appointment.type'].browse(body.get('type_id'))
            schedule_id = self.env['calendar.schedule'].search([('type_id','=',type_id.id), ('start','=',start_time_utc)])
            if schedule_id:
                # Update existing schedule only two values can change 
                vals = {
                    'scheduled_agents': int(body.get('scheduled_agents')), # number of agents supposed to be available for this
                    'forecasted_agents': int(body.get('forecasted_agents')), # May be implemented at a later date.
                }
                schedule_id.update(vals)
            else:
                # create new schedule
                vals = {
                    'name': type_id.name,
                    'start': start_time_utc,
                    'stop': stop_time_utc,
                    'duration': 30.0,
                    'scheduled_agents': int(body.get('scheduled_agents')), # number of agents supposed to be available for this. Can sometimes be float.
                    'forecasted_agents': int(body.get('forecasted_agents')), # May be implemented at a later date. Can sometimes be float.
                    'type_id': type_id.id,
                    'channel': type_id.channel.id,
                }
                schedule_id = self.env['calendar.schedule'].create(vals)
            # TODO: maybe move this
            schedule_id.create_occasions()
        
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_appointment.appointment_schedules').id:
            if not self.model_record or self.model_record._name != 'calendar.schedule':
                raise Warning("Appointment: Attached record is not an calendar.schedule! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record
            self.body = self.edi_type.type_mapping.format(
                path = "appointments/v1/resource-planning/competencies/schedules",
                from_date = obj.start.strftime("%Y-%m-%dT%H:%M:%SZ"), # 2020-03-17T00:00:00Z
                to_date = obj.stop.strftime("%Y-%m-%dT%H:%M:%SZ"), # 2020-03-25T00:00:00Z
                comp = obj.type_id.ipf_id, # ded72445-e5d3-4e21-a356-aad200dac83d
            )

            envelope = self.env['edi.envelope'].create({
                'name': 'Appointment schedules request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                # 'recipient': self.recipient.id,
                # 'sender': self.env.ref('base.main_partner').id,
                # 'application': app.name,
                # 'edi_message_ids': [(6, 0, msg_ids)]
                'edi_message_ids': [(6, 0, [self.id])]
            })

            # TODO: Decide if we want to fold here?
            # envelope.fold()
            
        else:
            super(edi_message, self).pack()
