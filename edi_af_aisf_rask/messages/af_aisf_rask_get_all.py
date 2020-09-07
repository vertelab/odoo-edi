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

import logging

_logger = logging.getLogger(__name__)

LOCAL_TZ = 'Europe/Stockholm'

class edi_message(models.Model):
    _inherit = 'edi.message'

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_rask.rask_get_all').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = dict(ast.literal_eval(self.body.decode("utf-8")))

            res_partner_obj = self.env['res.partner'].search([('customer_id', '=', body.customerId)])
            if res_partner_obj:
                if (self.messageType == "AnsvarigtKontor"):
                    office = body.get('kontor')
                    if office:
                        office_obj = self.env['res.partner'].search([('office_code', '=', office.get('kontorsKod'))])
                        if office_obj:
                            res_partner_obj.office = office_obj
                else:
                    pass
            else:
                # Skapa res_partner-objekt för den sökande
                anka = "pelle"
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_rask.rask_get_all').id:
            self.body = self.edi_type.type_mapping.format(
                path="arbetssokande/rest/v1/arbetssokande/{sokande_id}/anpassad?resurser=alla".format(sokande_id=self.sokandeId)
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'RASK all information request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
        else:
            super(edi_message, self).pack()
