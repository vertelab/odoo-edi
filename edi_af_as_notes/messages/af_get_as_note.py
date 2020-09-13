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
        if self.edi_type.id == self.env.ref('edi_af_as_notes.edi_af_as_notes_post').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = dict(ast.literal_eval(self.body.decode("utf-8")))
            
            #NOT IMPLEMENTED

            daily_note_id = False#self.env['calendar.schedule'].search([('type_id','=',type_id.id), ('start','=',start_time_utc)])
            if daily_note_id:
                # Update existing schedule only two values can change 
                vals = {
                    
                }
                daily_note_id.update(vals)
            else:
                # create new schedule
                vals = {

                }
                schedule_id = self.env['res.partner.notes'].create(vals)
            # TODO: maybe move this
            schedule_id.create_occasions()
        
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_as_notes.edi_af_as_notes_post').id:
            if not self.model_record or self.model_record._name != 'res.partner.notesq':
                raise Warning("Appointment: Attached record is not an daily note! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record
            self.body = self.edi_type.type_mapping.format(
                path = "",
                
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'Jobseeker Daily Note request',
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
