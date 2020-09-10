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
        if self.edi_type.id == self.env.ref('edi_af_as.asok_office').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))
            
            office_code = body.get('kontorsKod')
            _logger.warn("Unpack body: %s" % body)
            if office_code:
                jobseeker = self.env['res.partner'].search([('customer_id', '=', body.get('sokande_id'))])
                office_obj = self.env['res.partner'].search([('office_code', '=', office_code)])
                if office_obj:
                    vals = {
                        'office': office_obj.id,
                    }
                    jobseeker.write(vals)
                else:
                    pass
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_as.asok_office').id:
            if not self.model_record or self.model_record._name != 'res.partner' or not self.model_record.is_jobseeker:
                raise Warning("Appointment: Attached record is not a res.partner or not a jobseeker! {model}".format(model=self.model_record and self.model_record._name or None))

            obj = self.model_record #res.partner 
            self.body = self.edi_type.type_mapping.format(
                path = "ais-f-arbetssokande/v2/kontor/{sokande_id}".format(sokande_id = obj.customer_id)
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
