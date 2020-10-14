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
import ast

import logging
_logger = logging.getLogger(__name__)

class edi_message(models.Model):
    _inherit='edi.message'

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_trask.asok_contact').id:
            self.body = dict(ast.literal_eval(self.body.decode("utf-8")))
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_trask.asok_contact').id:
            if not self.model_record or self.model_record._name != 'res.partner':
                raise Warning("Attached record is not a res.partner or not a jobseeker! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record 
            body_dict = {}
            body_dict['base_url'] = self.edi_type.type_mapping.format(
                path = "ais-f-arbetssokande/v2/kontakt/{sokande_id}".format(sokande_id = obj.customer_id)
            )
            body_dict['method'] = 'PATCH'
            
            data_dict = {}
            if obj.last_contact and obj.last_contact_type:
                data_dict['senasteKontaktTyp'] = obj.last_contact_type # Possible values: B, T, E, P, I
                data_dict['senasteKontaktDatum'] = obj.last_contact.strftime("%Y-%m-%d") #"2019-10-02",
            if obj.next_contact:
                data_dict['nastaKontaktTyper'] = ["%s" % obj.next_contact_type] # Possible values: B, T, E, P, I
                data_dict['nastaKontaktDatum'] = obj.next_contact.strftime("%Y-%m-%d") #"2019-12-31",
                data_dict['nastaKontaktTid'] = obj.next_contact_time.strftime("%H:%M") #"11:30",
            body_dict['data'] = data_dict
            self.body = tuple(sorted(body_dict.items()))

            envelope = self.env['edi.envelope'].create({
                'name': 'asok contact update',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
        else:
            super(edi_message, self).pack()
