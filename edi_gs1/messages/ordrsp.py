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

def _check_order_status(order):
    for line in order.order_line:
        if line.product_uom_qty != line.order_qty:
            return 4
    return 29 #TODO: find correct code


class edi_message(models.Model):
    _inherit='edi.message'

    """
UNA:+.? '
UNB+UNOC:3+7301002000009:14+7310000000040:14+110131:1720+627++ICARSP4'
UNH+9+ORDRSP:D:93A:UN:EDIT30'
BGM+231::9+201101311720471+4'
DTM+137:20110131:102'
DTM+2:20110207:102'
FTX+ZZZ+1+001+Leveransdag framflyttad:201101311643:20110208:LD:64741'
RFF+CR:1101310181'
NAD+BY+7301004008461::9'
NAD+SU+7310000000040::9'
LIN+3+7'
PIA+5+125339:BP'
QTY+21:3'
UNS+S'
UNT+13+9'
UNZ+1+627'
"""

    """
UNH             EDIFACT-styrinformation.
BGM             Typ av Ordersvar.
DTM     Bekräftat leveransdatum.
FTX Uppgifter för felanalys
RFF- DTM    Referensnummer
NAD     Köparens identitet (EAN lokaliseringsnummer).
        Leverantörens identitet (EAN lokaliseringsnummer).

LIN     Radnummer.
            EAN artikelnummer.
PIA     Kompletterande artikelnummer.
QTY Kvantitet.

UNS     Avslutar orderrad.
UNT     Avslutar ordermeddelandet.
"""

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
                    msg += self.QVR(line)
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
            #TODO: What encoding should be used?
            self.body = base64.b64encode(self._gs1_encode_msg(msg))

    @api.one
    def _unpack(self):
        _logger.debug('unpack ORDRSP')
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_ordrsp').id:
            #Read ORDRSP corresponding to REPORD sent to ICA.
            segment_count = 0
            order_state = ''
            delivery_date = ''
            text = ''
            msg = ''
            order = None
            lines = []
            line = None
            error = False
            for segment in self._gs1_get_components():
                segment_count += 1
                for s in segment:
                    msg += s
                s += '\n'
                try:
                    if segment[0] == 'BGM':
                        if len(segment) > 3:
                            order_state = segment(3)
                    elif segment[0] == 'DTM':
                        if segment[1] == '2':
                            delivery_date = segment[2]
                    elif segment[0] == 'FTX':
                        ftx = segment[4]
                        #qualifier = ZZZ, function = 1, ref = 001
                        #Build human readable message from FTX field
                        header = ['Felmeddelande: ', 'Order skapad (ÅÅÅÅMMDDTTMM): ',
                            'Framflyttad leveransdag (ÅÅÅÅMMDD): ', 'Felkod', 'Kundens butiksnummer']
                        for i in range(len(ftx)):
                            if i < len(header):
                                text += header[i]
                            text += ftx[i] + '\n'
                    elif segment[0] == 'RFF' and segment[1] == 'CR':
                        order = self.env['sale.order'].search([('name', '=', segment[2])])[0]
                    elif segment[0] == 'NAD':
                        pass
                    elif segment[0] == 'LIN':
                        if line:
                            lines.append[line]
                        line = {
                            'sequence': segment[1],
                            'status': segment[2],
                        }
                        line['product'] = self._get_product(segment[3]).name
                    elif segment[0] == 'PIA' and line:
                        pass
                    elif segment[0] == 'QTY' and line:
                        line['quantity'] = segment[2]
                    elif segment[0] == 'UNS' and line:
                        lines.append[line]
                except:
                    error = True
            
            if error or not order:
                pass
            res = 'status: ' + order_state
            res += '\ndelivery date: ' + delivery_date
            res += '\n' + text
            res += '\n' + msg
            if lines:
                res += '\n' 
                for line in lines:
                    res += '\nline %s:\n\tproduct: %s\n\tquantity: %s\n\tstatus: %s\n' % (
                        line.get('sequence', ''), line.get('product', 'not found'),
                        line.get('quantity', ''),
                        'Not accepted' if line.get('status', '') == '7' else 'Unknown')
            res += '\n\noriginal message:\n' + msg
            
            raise Warning("ORDRSP is not implemented yet!")
        else:
            super(edi_message, self)._unpack()
