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
        if self.edi_type.id == self.env.ref('edi_af_facility.office_campus').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))           
            
            for office in body:
                office_id = '__ais_import__.dptmnt_office_%s' % office.get('office_code')
                partner_vals = {
                    'phone': office.get('phone_number'),
                    'fax': office.get('fax_number'),
                    'email': office.get('email_address')
                }
                
                external_xmlid = '__facility_import__.part_campus_%s' % office.get('campus.location_code')
                partner_obj = create_partner_from_dict(partner_vals, external_xmlid)

                external_xmlid_state = 'partner_view_360.state_se_%s' % office.get('campus.county_number')
                state_id = self.env['ir.model.data'].xmlid_to_res_id(external_xmlid_state)
                visitaiton_address_vals = {
                    'street': office.get('visiting_address.street'),
                    'zip': office.get('visiting_address.zip'),
                    'city': office.get('visiting_address.city'),
                    'state_id': state_id,
                }
                external_xmlid = '__facility_import__.part_campus_visitation_address_%s' % office.get('campus.location_code')
                visitation_address_obj = create_partner_from_dict(visitaiton_address_vals, external_xmlid)

                mailing_address_vals = {
                    'street': office.get('mailing_address.street'),
                    'zip': office.get('mailing_address.zip'),
                    'city': office.get('mailing_address.city'),
                }
                external_xmlid = '__facility_import__.part_campus_mailing_address_%s' % office.get('campus.location_code')
                mailing_address_obj = create_partner_from_dict(mailing_address_vals, external_xmlid)

                campus_vals = {
                    'name': office.get('name'),
                    'location_code': office.get('campus.location_code'),
                    'opening_hours': office.get('opening_hours'),
                    'personal_service_opening': office.get('personal_service_opening'),
                    'office_id': office_id.id,
                    'partner_id': partner_obj.id,
                    'visitation_address_id': visitation_address_obj.id,
                    'mailing_address_id': mailing_address_obj.id,
                } 
                external_xmlid = '__facility_import__.campus_%s' % campus_vals.get('work_place_code')
                campus_obj = self.env['hr.campus'].browse(self.env['ir.model.data'].xmlid_to_res_id(external_xmlid))
                if campus_obj:
                    campus_obj.write(campus_vals)
                else:
                    campus_obj = self.env['hr.campus'].create(campus_vals) 
                    external_xmlid = '__facility_import__.campus_%s' % campus_vals.get('work_place_code')
                    self.env['ir.model.data'].create(
                        {
                        'name': external_xmlid.split('.')[1], 
                        'module': external_xmlid.split('.')[0],
                        'model': campus_obj._name,
                        'res_id': campus_obj.id
                        })
        else:
            super(edi_message, self).unpack()
        
    @api.model
    def create_partner_from_dict(self, vals, external_xmlid):
        obj = self.env['res.partner'].browse(self.env['ir.model.data'].xmlid_to_res_id(external_xmlid))
        if obj:
            obj.write(vals)
        else:
            obj = self.env['res.partner'].create(vals) 
            self.env['ir.model.data'].create(
                {
                'name': external_xmlid.split('.')[1], 
                'module': external_xmlid.split('.')[0],
                'model': obj._name,
                'res_id': obj.id
                })  
        return obj 

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_facility.office_campus').id:
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
