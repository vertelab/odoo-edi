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
        if self.edi_type.id == self.env.ref('edi_af_appointment.appointment_ace_wi').id: 
            # decode string and convert string to tuple, convert tuple to dict
            body = dict(ast.literal_eval(self.body.decode("utf-8")))
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_appointment.appointment_ace_wi').id:
            if not self.model_record or self.model_record._name != 'edi.ace_workitem':
                raise Warning("Appointment: Attached record is not an edi.ace_workitem! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record
            body_dict = {}
            body_dict['base_url'] = self.edi_type.type_mapping.format(
                path = "appointments/v2/phone-appointments/queues/{queueId}/workitems".format(queueId=obj.queue.name),
            )
            body_dict['data'] = {
                'from': 'AFCRM',
                'subject': 'AFCRM %s' % obj.queue.name,
                'text': obj.text,
                'label': 'BokaMote',
                'errand': obj.errand.code,
                'customer': {
                    'id': {
                        'pnr': obj.appointment_id.partner_id.company_registry.replace('-', '')
                    },
                    'phone_mobile': (obj.appointment_id.partner_id.mobile or obj.appointment_id.partner_id.phone).replace(' ', ''),
                    'phone_home': obj.appointment_id.partner_id.phone.replace(' ', '')
                }
            }
            _logger.warn("body_dict: %s" % body_dict)
            self.body = tuple(sorted(body_dict.items()))

            envelope = self.env['edi.envelope'].create({
                'name': 'Appointment ACE WI post',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
            
        else:
            super(edi_message, self).pack()
