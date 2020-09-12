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
        if self.edi_type.id == self.env.ref('edi_af_facility.office_venue').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))           
            
            for office in body:
                campus_vals{
                    'type' : 'campus'
                    'street' : office.get('campus.name'),
                    'work_place_code' : office.get('campus.workplace_number'), 
                    'location_code' : office.get('campus.location_code'),
                } 
                external_xmlid = '__facility_import__.part_campus_%s' % campus_vals.get('work_place_code')
                campus_obj = self.env['res.partner'].browse (self.env['ir.model.data'].xmlid_to_res_id(external_xmlid))
                if campus_obj:
                    campus_obj.write(vals)
                else:
                    campus_obj = self.env['res.partner'].create(campus_vals) 
                    external_xmlid = '__facility_import__.part_campus_%s' % campus_vals.get('work_place_code')
                    self.env['ir.model.data'].create({
                                                'name': external_xmlid.split('.')[1],
                                                'module': external_xmlid.split('.')[0],
                                                'model': campus_obj._name,
                                                'res_id': campus_obj.id
                                                }) 

                vals = {
                    'name' : office.get('name'),
                    'office_code' : office.get('office_code'),
                } 
            self.env['res.partner'].browse (self.env['ir.model.data'].xmlid_to_res_id('__ais_import__.part_office_%s' % office.get('office_code')))
                office_obj = self.env['res.partner'].browse (self.env['ir.model.data'].xmlid_to_res_id('__ais_import__.part_office_%s' % office.get('office_code')))
                if office_obj:
                    office_obj.write(vals)
                else:
                    self.env['res.partner'].create(office_obj)                        
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_facility.office_venue').id:
            if not self.model_record or self.model_record._name != 'res.partner' or not self.model_record.is_jobseeker:
                raise Warning("Appointment: Attached record is not a res.partner or not a jobseeker! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record #res.partner 
            self.body = self.edi_type.type_mapping.format(
                path = "service-now-on-site-operations/v1/operations"
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'asok office request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                # 'recipient': self.recipient.id,
                # 'sender': self.env.ref('base.main_partner').id,
                # 'application': app.name,
                # 'edi_message_ids': [(6, 0, msg_ids)]
                'edi_message_ids': [(6, 0, [self.id])]
            })
        else:
            super(edi_message, self).pack()
