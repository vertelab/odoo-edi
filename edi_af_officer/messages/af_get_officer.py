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

    #TODO: add managerSignature as parent_id, if it doesn't exist create a new user with that login

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_officer.get_officer').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))
            i = 0
            for officer in body:
                i += 1
                if i == 500:
                    i = 0
                    self.env.cr.commit()
                workplaceNumber = officer.get('workplaceNumber')
                if workplaceNumber:
                    workplaceNumber = int(workplaceNumber)
                operation = self.env['hr.operation'].search([('workplace_number','=', workplaceNumber)])
                if not operation:
                    _logger.info("No operation with workplace number: %s" % workplaceNumber)
                office = self.env['hr.department'].search([('office_code','=',officer.get('officeCode'))])
                if not office:
                    _logger.info("office number %s not in database, creating" % officer.get('officeCode'))
                    office = self.env['hr.department'].create({'name': officer.get('officeCode'), 'office_code': officer.get('officeCode'), 'note': _('Missing in AIS-F')})
                if office and len(office) == 1:
                    parent_id = self.env['res.users'].search([('login','=',officer.get('managerSignature'))])
                    if not parent_id:
                        parent_id = self.env['res.users'].create({'name': officer.get('managerSignature')})
                    vals = {
                    'firstname': officer.get('firstName'),
                    'lastname': officer.get('lastName'),
                    'login': officer.get('userName'),
                    'email': officer.get('mail'),
                    'phone': officer.get('telephoneNumber'),
                    'mobile': officer.get('mobileNumber'),
                    'employee': True,
                    'saml_uid': officer.get('userName'),
                    'action_id': self.env.ref("hr_360_view.search_jobseeker_wizard").id,
                    'saml_provider_id': self.env['ir.model.data'].xmlid_to_res_id('auth_saml_af.provider_shibboleth'),
                    'parent_id': parent_id
                    }
                    user = self.env['res.users'].search([('login','=',vals['login'])])
                    employee_vals = {
                        'user_id': user.id,
                        'department_id': office.id,
                        'operation_id': operation.id,
                    }
                    
                    if user:
                        user.write(vals)
                        for employee in user.employee_ids:
                            employee.write(employee_vals)
                    else:
                        user = self.env['res.users'].create(vals)
                        employee_vals['user_id'] = user.id
                        self.env['hr.employee'].create(employee_vals)
                        external_xmlid = '__x500_import__.user_%s' % vals.get('login')
                        self.env['ir.model.data'].create({
                                    'name': external_xmlid.split('.')[1],
                                    'module': external_xmlid.split('.')[0],
                                    'model': user._name,
                                    'res_id': user.id
                                    }) 
                else:
                    _logger.warn("office number %s not found for %s, not creating" % (officer.get('officeCode'), officer.get('userName')))
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_officer.get_officer').id:
            if not self.model_record or self.model_record._name != 'hr.operation':
                raise Warning("Appointment: Attached record is not a hr.operation! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record #hr.operation 
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
