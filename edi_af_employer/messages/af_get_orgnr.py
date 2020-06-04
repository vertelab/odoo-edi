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

        _logger.warn("DAER: message: unpack: %s" % "Trying to unpack")
        if self.edi_type.id == self.env.ref('edi_af_employer.employers').id:
            # decode string and convert string to tuple 
            body = ast.literal_eval(self.body.decode("utf-8"))
            # convert tuple to dict
            body = dict(body)
            # schedule = self.body
            _logger.warn("DAER: body: %s" % body)
            # _logger.warn("DAER type(body): %s" % type(body))
            


            #start_time = datetime.strptime(body.get('start_time'), "%Y-%m-%dT%H:%M:%SZ")
            #stop_time = datetime.strptime(body.get('end_time'), "%Y-%m-%dT%H:%M:%SZ")

            # Integration gives us times in local (Europe/Stockholm) tz
            # Convert to UTC
            #start_time_utc = pytz.timezone(LOCAL_TZ).localize(start_time).astimezone(pytz.utc)
            #stop_time_utc = pytz.timezone(LOCAL_TZ).localize(stop_time).astimezone(pytz.utc)

            # schedules can exist every half hour from 09:00 to 16:00
            # check if calendar.schedule already exists 
            #type_id = self.env['calendar.appointment.type'].browse(body.get('type_id'))
            
            customer_id = self.env['res.partner'].browse(body.get('customer_nr'))  
            partner_id = self.env['calendar.schedule'].search([('customer_id', '=', customer_id)])
            if partner_id:
                # Update existing schedule only two values can change 
                vals = {
                    'company_registry': int(body.get('company_registry')), # number of agents supposed to be available for this
                }
                partner_id.update(vals)
            else:
                _logger.error("oh no the partner doesn't exist")
            # else:
            #     # create new schedule
            #     vals = {
            #         'name': type_id.name,
            #         'start': start_time_utc,
            #         'stop': stop_time_utc,
            #         'duration': 30.0,
            #         'scheduled_agents': int(body.get('scheduled_agents')), # number of agents supposed to be available for this. Can sometimes be float.
            #         'forecasted_agents': int(body.get('forecasted_agents')), # May be implemented at a later date. Can sometimes be float.
            #         'type_id': type_id.id,
            #         'channel': type_id.channel.id,
            #     }
            #     self.env['calendar.schedule'].create(vals)

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_employer.employers').id:
            if not self.model_record or self.model_record._name != 'res.partner':
                raise Warning("Appointment: Attached record is not an res.partner! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record
            self.body = self.edi_type.type_mapping.format(
                path = "", #replace with appropriate path #appointments/v1/resource-planning/competencies/schedules
                company_registry = obj.company_registry, # nått orgnummer
                comp = obj.type_id.ipf_id, # ded72445-e5d3-4e21-a356-aad200dac83d
            )

            envelope = self.env['edi.envelope'].create({
                'name': 'Organisation number request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                # 'recipient': self.recipient.id,
                # 'sender': self.env.ref('base.main_partner').id,
                # 'application': app.name,
                # 'edi_message_ids': [(6, 0, msg_ids)]
                'edi_message_ids': [(6, 0, [self.id])]
            })

            # envelope.fold()
            # TODO: finish
            
        else:
            super(edi_message, self).pack()

