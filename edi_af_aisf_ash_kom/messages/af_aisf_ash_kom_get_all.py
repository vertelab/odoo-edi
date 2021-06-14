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
from odoo import models, api, _
import ast
import json
import logging

_logger = logging.getLogger(__name__)

LOCAL_TZ = 'Europe/Stockholm'

class edi_message(models.Model):
    _inherit = 'edi.message'

    @api.one
    def unpack(self):
        """
        Updates a department with employees
        if an employee can't be found create it.
        """
        if self.edi_type.id == self.env.ref('edi_af_aisf_ash_kom.ash_kom_get_all').id:
            body = json.loads(self.body)
            office_vals = body.get('kontor')
            if office_vals:
                department_obj = self.env['hr.department'].search([(
                    'office_code',
                    '=',
                    office_vals.get('kontorKod')
                )])
                state_id = self.env['res.country.state'].search([
                    (
                        'code',
                        '=',
                        office_vals.get('kommunKod')
                    )
                ])
                partner_vals = { # partner for aditional information
                    'name': office_vals.get('namn'),
                    'email': office_vals.get('externEpost'),
                    'phone': office_vals.get('telefonnummer'),
                    'street': office_vals.get('besoksadress'),
                    'street2': office_vals.get('utdelningsadress'),
                    'zip': office_vals.get('postnummer'),
                    'city': office_vals.get('postort'),
                    'state_id': state_id.id if state_id else False
                }
                if not department_obj:
                    department_obj = self.env['hr.department'].create({
                        'name': office_vals.get('namn'),
                        'office_code': office_vals.get('kontorKod')
                    })
                    external_xmlid = '__ais-f_import__.office_%s' % office_vals.get(
                        'kontorKod'
                    )
                    self.env['ir.model.data'].create({
                        'name': external_xmlid.split('.')[1],
                        'module': external_xmlid.split('.')[0],
                        'model': department_obj._name,
                        'res_id': department_obj.id
                    })
                partner_id = department_obj.partner_id
                if not partner_id:
                    partner_id = self.env['res.partner'].create(partner_vals)
                    department_obj.write({
                        'partner_id': partner_id
                    })
                else:
                    partner_id.write(partner_vals)
                department_obj.write({'name': office_vals.get('namn')})
                employee_ids = []
                for employee in body.get('handlaggare').get('handlaggare'):
                    sign = employee.get('signatur')
                    user = self.env['res.users'].search([(
                        'login',
                        '=',
                        sign
                    )])
                    if not user:
                        user = self.env['res.users'].with_context(no_reset_password=True).create({
                            'login': sign,
                            'firstname': employee.get('fornamn'),
                            'lastname': employee.get('efternamn'),
                            'saml_uid': sign,
                            'saml_provider_id':
                                self.env['ir.model.data'].xmlid_to_res_id(
                                    'auth_saml_af.provider_shibboleth'
                                ),
                            'tz': 'Europe/Stockholm',
                            'lang': 'sv_SE',
                            'groups_id': [
                                (
                                    6,
                                    0,
                                    [self.env.ref('base.group_user').id]
                                )
                            ],
                            'employee': True,
                            'employee_ids': [(0, 0, {
                                'firstname': employee.get('fornamn'),
                                'lastname': employee.get('efternamn'),
                                })]
                            })
                        _logger.debug("User %s missing, adding" % sign)
                        external_xmlid = '__ais-f_import__.user_%s' % sign
                        self.env['ir.model.data'].create({
                            'name': external_xmlid.split('.')[1],
                            'module': external_xmlid.split('.')[0],
                            'model': user._name,
                            'res_id': user.id
                        })
                    employee_ids.append(user.employee_ids._ids)
                department_obj.write({
                    'employee_ids': [(6, 0, employee_ids)]
                })
            else:
                _logger.error('No "kontor" in body')
        else:
            super(edi_message, self).unpack()

            

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_ash_kom.ash_kom_get_all').id:
            obj = self.model_record

            self.body = self.edi_type.type_mapping.format(
                path="ash-kontor-och-medarbetare/v1/kontor/"
                     "{office_code}/handlaggare".format(
                        office_code=obj.office_code)
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'ASH KOM all information request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
        else:
            super(edi_message, self).pack()
