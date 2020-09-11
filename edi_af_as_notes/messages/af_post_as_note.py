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

class edi_message(models.Model):
    _inherit='edi.message'
            
    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_as_notes.edi_af_as_notes_post').id: 
            # decode string and convert string to tuple, convert tuple to dict
            body = dict(ast.literal_eval(self.body.decode("utf-8")))
            _logger.warn("RAPID reply: %s" % body)
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_as_notes.edi_af_as_notes_post').id:
            if not self.model_record or self.model_record._name != 'res.partner.notes' or not self.model_record.partner_id.is_jobseeker:
                raise Warning("Appointment: Attached record is not an daily note! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record
            body_dict = {}
            body_dict['base_url'] = self.edi_type.type_mapping.format(
                path = "ais-f-daganteckningar/v1/anteckning",
            )
            body_dict['data'] = {
                "entitetsId": obj.customer_id, 
                "anteckningtypId": obj.note_type.name,
                "handelsetidpunkt": obj.note_date.strftime("%Y-%m-%d"),
                "ansvarKontor": obj.office.office_code,
                "ansvarSignatur": obj.administrative_officer.login,
                "avsandandeSystem": "CRM", 
                "avsandandeSystemReferens": "null",
                "lank": "null",
                "text": obj.note,
                "rubrik": obj.name,
                "redigerbar": "A",
                "sekretess": 'true' if obj.is_confidential else 'false',
                "samtycke": 'false'
            }
            #_logger.info('administrative_officer login: %s' % obj.administrative_officer)
            #_logger.info(body_dict['data'])
            self.body = tuple(sorted(body_dict.items()))

            envelope = self.env['edi.envelope'].create({
                'name': 'Jobseeker daily note post',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
            
        else:
            super(edi_message, self).pack()
