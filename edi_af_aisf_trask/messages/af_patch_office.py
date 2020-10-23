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

import logging
_logger = logging.getLogger(__name__)

class edi_message(models.Model):
    _inherit='edi.message'

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_trask.asok_patch_office').id:
            pass
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_trask.asok_patch_office').id:
            if not self.model_record or self.model_record._name != 'res.partner' or not self.model_record.is_jobseeker:
                raise Warning("Attached record is not a res.partner or not a jobseeker! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record
            office_code = self.env.context.get('office_code')
            body_dict = {}
            body_dict['base_url'] = self.edi_type.type_mapping.format(
                path = "ais-f-arbetssokande/v2/kontor/{sokande_id}".format(sokande_id = obj.customer_id)
            )
            body_dict['method'] = 'PATCH'
            data_dict = {}
            data_dict['ansvarigHandlaggareSignatur'] = obj.user_id.af_signature
            if office_code:
                data_dict['kontorsKod'] = office_code
            body_dict['data'] = data_dict
            self.body = json.dumps(body_dict)

            envelope = self.env['edi.envelope'].create({
                'name': 'asok office request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
        else:
            super(edi_message, self).pack()
