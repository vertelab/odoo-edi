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
import sys
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)

def _check_order_status(order):
    for line in order.order_line:
        if line.product_uom_qty != line.order_qty:
            return 4
    return 29 #TODO: find correct code


class edi_message(models.Model):
    _inherit='edi.message'

    @api.one
    def _pack(self):
        _logger.debug('pack ORDRSP')
        super(edi_message, self)._pack()
        msg = None
        #Orderbekräftelse
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_ordrsp').id:
            _logger.debug('pack Orderbekräftelse. model_record: %s' % self.model_record)
            if self.model_record._name != 'sale.order':
                raise ValueError("ORDRSP: Attached record is not a sale.order! {model}".format(model=self.model_record._name),self.model_record._name)
            order = self.model_record
            status = _check_order_status(order)
            msg = self.UNH('ORDRSP')
            msg += self.BGM(231, order.name, status=status)
            msg += self.DTM(137, format=203)  # Order Response Date
            msg += self.DTM(76, dt=order.date_order, format=203) # Planned Delivery Date
            #FTX?
            msg += self.RFF(order.client_order_ref or order.name, 'ON')
            msg += self.NAD_BY(order.partner_id)
            msg += self.NAD_SU()
            cnt_lines = 0
            cnt_amount = 0
            for line in order.order_line:
                # Only send lines that have changes
                if line.product_uom_qty != line.order_qty:
                    cnt_lines += 1
                    cnt_amount += line.product_uom_qty
                    msg += self.LIN(line)
                    msg += self.PIA(line.product_id, 'SA')
                    msg += self.QTY(line)
                    msg += self.QVR(line.product_uom_qty - line.order_qty)
                    msg += self.RFF(order.client_order_ref or order.name, 'ON', line.sequence)
                else:
                    self._lin_count += 1
            msg += self.UNS()
            if cnt_lines > 0:
                msg += self.CNT(1, cnt_amount)
                msg += self.CNT(2, cnt_lines)
            msg += self.UNT()

        #Ordererkännande
        elif self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_orderk').id:
            _logger.debug('pack Ordererkännande. mode_record: %s' % self.model_record)
            if self.model_record._name != 'sale.order':
                raise ValueError("ORDRSP: Attached record is not a sale.order!")
            order = self.model_record
            msg =  self.UNH(edi_type='ORDRSP')
            msg += self.BGM(231, order.name, 12)
            msg += self.DTM(137,format=203)
            if order.note:
                msg += self.FTX(order.note)
            msg += self.RFF(order.client_order_ref or order.name, 'ON')
            msg += self.NAD_BY(order.partner_id)
            msg += self.NAD_SU()
            msg += self.UNS()
            msg += self.UNT()
        if msg:
            self.body = base64.b64encode(self._gs1_encode_msg(msg))

    @api.one
    def _unpack(self):
        _logger.debug('unpack ORDRSP')
        #~ if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_ordrsp').id:
            #~ #Do stuff
        #~ 
        super(edi_message, self)._unpack()
