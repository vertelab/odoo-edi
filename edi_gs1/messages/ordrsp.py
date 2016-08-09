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
        _logger.info('pack ORDRSP')
        super(edi_message, self)._pack()
        msg = None
        #Orderbekräftelse
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_ordrsp').id:
            _logger.warn('mode_record: %s' % self.model_record)
            if self.model_record._name != 'sale.order':
                raise ValueError("ORDRSP: Attached record is not a sale.order! {model}".format(model=self.model_record._name),self.model_record._name)
            order = self.model_record
            status = _check_order_status(order)
            msg = self.UNH('ORDRSP')
            msg += self.BGM(231, order.name, status=status)
            msg += self.DTM(137, format=203)  # Order Response Date
            msg += self.DTM(76, dt=order.date_order, format=203) # Planned Delivery Date
            #FTX?
            msg += self.RFF(order.client_order_ref, 'ON')
            msg += self.NAD_BY()
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
                    msg += self.RFF(order.client_order_ref, 'ON', self._lin_count * 10)
                else:
                    self._lin_count += 1
            msg += self.UNS()
            if cnt_lines > 0:
                msg += self.CNT(1, cnt_amount)
                msg += self.CNT(2, cnt_lines)
            msg += self.UNT()

        #Ordererkännande
        elif self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_orderk').id:
            _logger.warn('mode_record: %s' % self.model_record)
            if self.model_record._name != 'sale.order':
                raise ValueError("ORDRSP: Attached record is not a sale.order!")
            msg =  self.UNH(edi_type='ORDRSP')
            msg += self.BGM(231, self.model_record.name, 12)
            msg += self.DTM(137,format=203)
            if self.model_record.note:
                msg += self.FTX(self.model_record.note)
            msg += self.RFF(self.model_record.client_order_ref or '', 'ON')
            msg += self.NAD_BY()
            msg += self.NAD_SU()
            msg += self.UNS()
            msg += self.UNT()
        if msg:
            #TODO: What encoding should be used?
            self.body = base64.b64encode(self._gs1_encode_msg(msg))

    @api.one
    def _unpack(self):
        _logger.info('unpack ORDRSP')
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_ordrsp').id:
            segment_count = 0
            delivery_dt = None
            #Delivered by?
            delivery_prom_dt = None
            #Message sent date?
            doc_dt = None
            order_values = {}
            order_values['order_line'] = []
            line = {}
            for segment in self._gs1_get_components():
                segment_count += 1
                _logger.warn('segment: %s' % segment)
                #Begin Message
                if segment[0] == 'BGM':
                    self.name = segment[2]
                    order_values['client_order_ref'] = segment[2]
                #Datetime
                elif segment[0] == 'DTM':
                    function = segment[1][0]
                    if function == '2':
                        delivery_dt = self._parse_date(segment[1])
                    elif function == '69':
                        #Is this the correct date to use???
                        order_values['date_order'] = self._parse_date(segment[1])
                    elif function == '137':
                        doc_dt = self._parse_date(segment[1])
                elif segment[0] == 'NAD':
                    if segment[1] == 'BY':
                        order_values['partner_id'] = self._get_partner(segment[2]).id
                    elif segment[1] == 'SU':
                        supplier = self._get_partner(segment[2])
                        _logger.warn('supplier: %s' % segment[2])
                    elif segment[1] == 'SN':
                        store_keeper = self._get_partner(segment[2])
                        #ICA Sverige AB
                        _logger.warn('store keeper: %s' % segment[2])
                    elif segment[1] == 'CN':
                        consignee = self._get_partner(segment[2])
                        _logger.warn('consignee: %s' % segment[2])
                    #Delivery Party
                    elif segment[1] == 'DP':
                        recipient = self.env['edi.envelope']._get_partner(segment[2])
                        _logger.warn('recipient: %s' % segment[2])
                elif segment[0] == 'LIN':
                    if line:
                        order_values['order_line'].append((0, 0, line))
                    line = {'product_id': self._get_product(segment[3]).id}
                elif segment[0] == 'QTY':
                    line['product_uom_qty'] = line['order_qty'] = self._parse_quantity(segment[1])
                #Alternative Product Identification
                elif segment[0] == 'PIA':
                    pass
                #Free text
                #~ #elif segment[0] == 'FTX':
                #~ #    pass
                #~ #elif segment[0] == 'RFF':
                    #~ #CR customer reference number
                    #~ #GN Government Reference Number
                    #~ #VA VAT registration number
                #~ #    pass
                #End of message
                elif segment[0] == 'UNT':
                    if segment_count != int(segment[1]):
                        raise TypeError('Wrong number of segments! %s %s' % (segment_count, segment),segment)
                    #Add last line
                    if line:
                        order_values['order_line'].append((0, 0, line))
                    _logger.warn(order_values)
                    #create order
                    order = self.env['sale.order'].create(order_values)
                    self.model = order._name
                    self.res_id = order.id
        else:
            super(edi_message, self)._unpack()
