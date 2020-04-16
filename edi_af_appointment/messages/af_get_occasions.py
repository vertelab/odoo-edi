# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
import json

import logging
_logger = logging.getLogger(__name__)

class edi_message(models.Model):
    _inherit='edi.message'
            
    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_appointment.edi_af_get_occasions').id:
            pass
           #  might not be needed
           # result = sel.body
           # result = json.loads(result)

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_appointment.edi_af_get_occasions').id:
 #           if not self.model_record or self.model_record._name != 'account.invoice':
 #               raise Warning("Appointment: Attached record is not an account.invoice! {model}".format(model=self.model_record and self.model_record._name or None))
            obj = self.model_record

            params = self.edi_type.type_mapping.format(
                from_date_str = obj.from_date.strftime("%Y-%m-%d"), # 2020-03-17
                to_date_str = obj.to_date.strftime("%Y-%m-%d"), # 2020-03-25
                appointment_channel_str = obj.appointment_channel, # 'SPD'
                appointment_type_str = obj.appointment_type, # '1'
                max_depth_str = ("&max_depth=%s" % obj.max_depth) if obj.max_depth else '',
                appointment_length_str = ("&appointment_length=%s" % obj.appointment_length) if obj.appointment_length else '',
                location_code_str = ("&location_code=%s" % obj.location_code) if obj.location_code else '',
                profession_id_str = ("&profession_id=%s" % obj.profession_id) if obj.profession_id else '',
            )

            self.body = params
        else:
            super(edi_message, self).pack()

