# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution, third party addon
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
import base64
from datetime import datetime
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)


class edi_message(models.Model):
    _inherit = 'edi.message'

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

    def _unpack(self):
        _logger.info('unpack (orders.py) %s %s' % (self.edi_type, self))
        super(edi_message, self)._unpack()
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_orders').id:
            segment_count = 0
            warnings = ''
            #Delivered by?
            delivery_prom_dt = None
            doc_dt = None
            order_values = {
                #'edi_type': 'esap20',
                'order_line': [],
                'unb_sender': self.sender.id,
                'unb_recipient': self.recipient.id,
                'route_id': self.route_id.id,
            }
            line = {}
            for segment in self._gs1_get_components():
                segment_count += 1
                #~ _logger.warn('segment: %s' % segment)
                #Begin Message
                if segment[0] == 'BGM':
                    order_values['client_order_ref'] = segment[2]
                #Datetime
                elif segment[0] == 'DTM':
                    function = segment[1][0]
                    if function == '2':
                        order_values['dtm_delivery'] = self._parse_date(segment[1])
                        order_values['date_order'] = self._parse_date(segment[1])
                        #~ _logger.warn(order_values['date_order'])
                        if segment[1][2] == '102':
                            order_values['date_order'] = order_values['date_order'][:11] + '15' + order_values['date_order'][13:]
                            order_values['dtm_delivery'] = order_values['dtm_delivery'][:11] + '15' + order_values['dtm_delivery'][13:]
                        #~ _logger.warn(order_values['date_order'])
                    elif function == '137':
                        order_values['dtm_issue'] = self._parse_date(segment[1])
                        if segment[1][2] == '102':
                            order_values['dtm_issue'] = order_values['dtm_issue'][:11] + '15' + order_values['dtm_issue'][13:]
                elif segment[0] == 'NAD':
                    if segment[1] == 'BY':
                        order_values['nad_by'] = order_values['partner_id'] = self._get_partner(segment[2]).id
                        self.consignee_id = self._get_partner(segment[2]).id
                    elif segment[1] == 'SU':
                        order_values['nad_su'] =self._get_partner(segment[2]).id
                        supplier = self._get_partner(segment[2])
                        if self.env.ref('base.main_partner').id != self._get_partner(segment[2]).id:
                            raise ValueError('Supplier %s is not us (%s)' % (segment[2],self.env.ref('base.main_partner').gs1_gln))
                        #~ _logger.warn('supplier: %s' % segment[2])
                        self.consignor_id = self._get_partner(segment[2]).id
                    elif segment[1] == 'SN':
                        order_values['nad_sn'] =self._get_partner(segment[2]).id
                        store_keeper = self._get_partner(segment[2])
                        #ICA Sverige AB
                        #~ _logger.warn('store keeper: %s' % segment[2])
                    elif segment[1] == 'CN':
                        order_values['nad_cn'] =self._get_partner(segment[2]).id
                        self.consignee_id = self._get_partner(segment[2]).id
                        #~ _logger.warn('consignee: %s' % segment[2])
                    #Delivery Party
                    elif segment[1] == 'DP':
                        recipient = self._get_partner(segment[2]).id
                        order_values['nad_dp'] =self._get_partner(segment[2]).id
                        #~ _logger.warn('recipient: %s' % segment[2])
                    #Invoice Party
                    elif segment[1] == 'ITO':
                        recipient = self._get_partner(segment[2]).id
                        order_values['nad_ito'] =self._get_partner(segment[2]).id
                        #~ _logger.warn('invoice: %s' % segment[2])
                elif segment[0] == 'LIN':
                    if line:
                        order_values['order_line'].append((0, 0, line))
                    line = {'sequence': int(segment[1])}
                    try:
                        line['product_id'] = self._get_product(segment[3]).id
                    except:
                        warnings += 'Product not found: %s' % l
                elif segment[0] == 'QTY':
                    line['product_uom_qty'] = line['order_qty'] = self._parse_quantity(segment[1])
                #Alternative Product Identification
                elif segment[0] == 'PIA':
                    try:
                        product = self._get_product(segment[2])
                        if product and line:
                            if line.get('product_id', product.id) != product.id:
                                warnings += "Found two products for one line: %s and %s. %s" % (line['product_id'], product.id, line)
                            else:
                                line['product_id'] = product.id
                    except:
                        warnings += 'Product not found: %s' % l
                #Free text
                #~ #elif segment[0] == 'FTX':
                #~ #    pass
                elif segment[0] == 'RFF':
                    #CR customer reference number
                    #GN Government Reference Number
                    #VA VAT registration number
                    # CT Contract number
                    if len(segment[1]) > 1 and segment[1][0] == 'CT':
                        contract = self._get_contract(segment[1][1])
                        if contract:
                            order_values['project_id'] = contract
                #End of message
                elif segment[0] == 'UNT':
                    if segment_count != int(segment[1]):
                        raise TypeError('Wrong number of segments! %s %s' % (segment_count, segment),segment)
                    #Add last line
                    if line:
                        order_values['order_line'].append((0, 0, line))
                    _logger.warn(order_values)
                    for a, b, line in order_values['order_line']:
                        if not line.get('product_id'):
                            raise Warning(warnings)
                    #create order
                    order = self.env['sale.order'].create(order_values)
                    if order.nad_ito:
                        self.nad_ito = order.nad_ito.id
                        order.partner_invoice_id = order.nad_ito.id
                    elif not order.partner_invoice_id.id == order.partner_id.id:
                        self.nad_ito = order.partner_invoice_id.id
                        order.nad_ito = order.partner_invoice_id.id
                    if order.nad_dp:
                        self.nad_dp = order.nad_dp.id
                        order.partner_shipping_id = order.nad_dp.id
                    elif not order.partner_shipping_id.id == order.partner_id.id:
                        self.nad_dp = order.partner_shipping_id.id
                        order.nad_dp = order.partner_shipping_id.id
                    if warnings:
                        self.log(warnings)
                    _logger.info('Order ready %r' % order)
                    self.model = order._name
                    self.res_id = order.id
