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
import json

import logging
_logger = logging.getLogger(__name__)

# messages with bodies like this:
#  {'currency': 'EUR', 'date': '2020-05-14', 'rate': '10.32' }
#  {'currency': 'USD', 'date': '2020-05-14', 'rate': '10.32' }
#  {'currency': 'GBP', 'date': '2020-05-14', 'rate': '10.32' }
#


class edi_message(models.Model):
    _inherit='edi.message'
            
    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_currency.get_echange_rates').id:
            rec = json.loads(self.body)
            currency = self.env['res.currency'].search([('name','=',rec.get('currency',None))])
            self.env['res.currency.rate'].create({'currency_id': currency.id, 'name': rec.get('date'),'rate': rec.get('rate')})
        else:
            super(edi_message, self).unpack()
    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_currency.get_echange_rates').id:
            if not self.model_record or self.model_record._name != 'res.currency.rate':
                raise Warning("Exchange Rates: Attached record is not an res.currency.rate! {model}".format(model=self.model_record and self.model_record._name or None))
            currency_rate = self.model_record
            self.body = self.edi_type.type_mapping.format(
                date = obj.name.strftime("%Y-%m-%d"), 
                rate = obj.rate, 
                currency = obj.currency_id.name,
            )
        else:
            super(edi_message, self).pack()

