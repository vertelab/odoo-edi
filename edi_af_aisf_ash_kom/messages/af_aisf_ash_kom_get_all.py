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
            department_obj = self.env['hr.department'].search([(
                'office_code',
                '=',
                body.get('kontor').get('kontorKod')
            )])

            employee_ids = []
            for employee in body.get('handlaggare'):
                sign = employee.get('handlaggare').get('signatur')
                user = self.env['res.users'].search([(
                    'login',
                    '=',
                    sign
                )])
                if not user:
                    user = self.env['res.users'].create({
                        'login': sign,
                        'name': sign,
                        'employee_ids': [(0,0,{
                            'name': sign
                            })]
                        })
                    _logger.warn("User %s missing, adding" % sign)
                employee_ids.append(user.employee_ids._ids)

            department_obj.write({
                'employee_ids': [(6,0,employee_ids)]
            })

            

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_ash_kom.ash_kom_get_all').id:
            obj = self.model_record

            self.body = self.edi_type.type_mapping.format(
                path="ash-kontor-och-medarbetare/v1/kontor/{office_code}/handlaggare".format(
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
