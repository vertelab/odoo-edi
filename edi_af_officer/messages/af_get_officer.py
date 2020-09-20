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
        if self.edi_type.id == self.env.ref('edi_af_officer.get_officer').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))
            for officer in body:
                location = self.env['hr.location'].search([('workplace_number','=', officer.get('workPlaceNumber'))])
                office = self.env['hr.department'].search([('office_code','=',officer.get('officeCode'))])
                vals = {
                    'firstname': officer.get('firstName'),
                    'lastname': officer.get('lastName'),
                    'login': officer.get('userName'),
                    'email': officer.get('mail'),
                    'phone': officer.get('telephoneNumber'),
                    'mobile': officer.get('mobileNumber'),
                    'office_id': office.id,
                    'location_id': location.id
                }
                #     {
                #     "id" : "32d2a8d6-b521-c391-d018-a5bb762d4d59",
                #     "lastName" : "Svensson",
                #     "firstName" : "Sven",
                #     "userName" : "abcde",
                #     "mail" : "sven.svenssondok@arbetsformedlingen.se",
                #     "managerId" : "32d2a8d6-b521-c391-d018-a5bb762d4d59",
                #     "managerSignature" : "cheft",
                #     "telephoneNumber" : "01012345678",
                #     "personalIdentityNumber" : "191111111111",
                #     "startDate" : "2019-02-01",
                #     "functionCode" : "0123",
                #     "workPlaceNumber" : "01900",
                #     "organisationNumber" : "0130_73100704",
                #     "endDate" : "2022-12-31",
                #     "functionName" : "Testare",
                #     "officeCode" : "3614",
                #     "mobileNumber" : "0701234567",
                #     "updated" : "2019-02-09T14:09:48.000+00:00",
                #     "loaStart" : "2020-01-01",
                #     "loaEnd" : "2020-04-01"
                #   },
                user = self.env['res.users'].search([('login','=',vals['login'])])
                if user:
                    user.write(vals)
                else:
                    user = self.env['res.users'].create(vals)
                    external_xmlid = '__x500_import__.user_%s' % vals.get('login')
                    self.env['ir.model.data'].create({
                                'name': external_xmlid.split('.')[1],
                                'module': external_xmlid.split('.')[0],
                                'model': user._name,
                                'res_id': user.id
                                }) 
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_officer.get_officer').id:
            if not self.model_record or self.model_record._name != 'hr.location':
                raise Warning("Appointment: Attached record is not a hr.location! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record #hr.location 
            self.body = self.edi_type.type_mapping.format(
                path = "x500-af-person/v1/af-persons",
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
