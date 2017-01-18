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
from openerp import models, fields, api, _
import base64
from datetime import datetime
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)

class edi_message(models.Model):
    _inherit='edi.message'
    
    @api.one
    def _pack(self):
        super(edi_message, self)._pack()
        if self.edi_type.id == self.env.ref('edi_gs1_repord.edi_message_type_repord').id:
            if self.model_record._name != 'rep.order':
                raise ValueError("REPORD: Attached record is not a rep.order! {model}".format(model=self.model_record._name),self.model_record._name)
            order = self.model_record
            order.client_order_ref = self.name_to_number(order.name)
            msg = self.UNH('ORDERS', ass_code='EDIT30', release='93A')
            msg += self.BGM('22E', order.client_order_ref)
            msg += self.DTM(137)
            msg += self.DTM(2, order.date_order)
            msg += self.NAD_BY(order.partner_id)
            #OB = client/supplier (Beställare, leverantör). Weird, but it's how ICA wants it.
            msg += self._NAD('OB', order.company_id and order.company_id.partner_id or self.env.ref('base.main_partner'))
            cnt_lines = 0
            cnt_amount = 0.0
            for line in order.order_line:
                cnt_lines += 1
                cnt_amount += line.product_uom_qty
                #~ if order.order_type != '3rd_party':
                    #~ msg += self.LIN()
                    #~ msg += self.PIA(line.product_id, 'SA')
                #~ else:
                msg += self.LIN()
                msg += self.PIA(line.product_id, 'BP', self.model_record.partner_id)
                msg += self.QTY(line)
            msg += self.UNS()
            if cnt_lines > 0:
                msg += self.CNT(1, cnt_amount)
                msg += self.CNT(2, cnt_lines)
            msg += self.UNT()
            self.body = base64.b64encode(self._gs1_encode_msg(msg))
