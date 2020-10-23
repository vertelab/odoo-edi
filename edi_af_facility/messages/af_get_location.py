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

class ediServiceNowOperation(models.Model):
    _name = "edi.service_now_operation"

    name = fields.Char(string="Name")
    

    department_id = fields.Many2one(comodel_name='hr.department', string="Department")
    location_id = fields.Many2one(comodel_name='hr.location', string="Location")
    operation_id = fields.Many2one(comodel_name="hr.operation", string="Operation")

    opening_hours = fields.Char()
    personal_service_opening = fields.Char()
    office_code = fields.Char()
    organisational_belonging = fields.Char()
    accessibilies = fields.Char()
    active = fields.Char()
    name = fields.Char()
    phone_hours = fields.Char()
    fax_number = fields.Char()
    email_address = fields.Char()
    phone_number = fields.Char()
    operation_id = fields.Char()
    last_operation_day = fields.Char()
    public_contact_name = fields.Char()
    public_contact_source = fields.Char()
    public_contact_user_name = fields.Char()
    visiting_address_street = fields.Char()
    visiting_address_zip = fields.Char()
    visiting_address_city = fields.Char()
    mailing_address_street = fields.Char()
    mailing_address_zip = fields.Char()
    mailing_address_city = fields.Char()
    campus_name = fields.Char()
    campus_workplace_number = fields.Char()
    campus_location_code = fields.Char()
    campus_county_number = fields.Char()
    campus_latitude = fields.Char()
    campus_longitude = fields.Char()
    x500_id = fields.Char()
    organisational_belonging_u_copakod = fields.Char()
    phone_numbers = fields.Char()
    public_contact = fields.Char()
    accessibilities = fields.Char()
    
    @api.one
    def compute_department_id(self):
        department = self.env['hr.department'].search([('office_code','=', self.office_code)])
        if department:
            self.department_id = department.id
        else:
            _logger.info("office number %s not in database, creating" % self.office_code)
            self.department_id = self.env['hr.department'].create({'name': self.office_code, 'office_code': self.office_code, 'note': _('Missing in AIS-F')}).id

    @api.one
    def compute_accessibilies(self, operation_id, accessibility_list):
        for accessibility in accessibility_list:
            accessibility['operation_id'] = operation_id
            self.env['hr.location.accessibility'].create(
                {
                    'operation_id': accessibility['operation_id'],
                    'name': accessibility['type'],
                    'description': accessibility['description']
                })

    @api.one
    def compute_location_id(self, department_id):
        location = self.env['hr.location'].search([('location_code', '=', self.campus_location_code)])
        operation = self.env['hr.operation'].search([('operation_code','=',self.x500_id)])
        #create partners from fields
        visitation_address_vals = {
            'type': 'visitation address',
            'street': self.visiting_address_street,
            'city': self.visiting_address_city,
            'zip': self.visiting_address_zip,
        }
        visitation_address = self.env['res.partner'].create(visitation_address_vals)
        mailing_address_vals = {
            'type': 'mailing address',
            'street': self.mailing_address_street,
            'city': self.mailing_address_city,
            'zip': self.mailing_address_zip,
        }
        mailing_address = self.env['res.partner'].create(mailing_address_vals)

        partner_vals = {
            'name': self.name,
            'phone': self.phone_number,
            'fax': self.fax_number,        
        }

        partner = self.env['res.partner'].create(partner_vals)

        operation_vals = {
            'name': self.name,
            'visitation_address_id': visitation_address.id,
            'mailing_address_id': mailing_address.id,
            'partner_id': partner.id,
            'opening_hours': self.opening_hours,
            'personal_service_opening': self.personal_service_opening,
            'operation_code': self.x500_id,
            'department_id': department_id.id
        }
        if operation:
            operation.write(operation_vals)
        else:
            operation = self.env['hr.operation'].create(operation_vals)
        
        location_vals = {
            'name': self.campus_name,
            'workplace_number': self.campus_workplace_number,
            'location_code': self.campus_location_code,
            'visitation_address_id': visitation_address.id,
        }
        
        if location:
            _logger.info("operation: %s location.operation_ids: %s" % (operation, location.operation_ids))
            if not operation in location.operation_ids:
                location.operation_ids = [(4, operation.id, 0)]
            location.write(location_vals)
        else:
            location_vals['operation_ids'] = [(4, operation.id, 0)]
            location = self.env['hr.location'].create(location_vals)
            external_xmlid = "__facility_import__.location_%s" % location_vals['location_code']
            self.env['ir.model.data'].create({
                            'name': external_xmlid.split('.')[1],
                            'module': external_xmlid.split('.')[0],
                            'model': location._name,
                            'res_id': location.id
                            })




class edi_message(models.Model):
    _inherit='edi.message'

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_facility.office_campus').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))   

            for operation_rec in body:
                vals = {}
                for key in operation_rec.keys():
                    vals[key.replace('.','_')] = operation_rec[key]
                vals['accessibilities'] = "%s" % vals['accessibilities']
                if operation_rec['active'] == 'true':
                    operation = self.env['edi.service_now_operation'].create(vals)
                    operation.compute_department_id()
                    operation.compute_location_id(operation.department_id)
                    #logg operation_id and location_id
                    operation.compute_accessibilies(operation.operation_id, operation_rec['accessibilities'])
        else:
            super(edi_message, self).unpack()
        
    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_facility.office_campus').id:
            if not self.model_record or self.model_record._name != 'hr.department':
                raise Warning("Appointment: Attached record is not a hr.department {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record  
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
