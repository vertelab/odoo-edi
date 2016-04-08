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
from edifact.helpers import separate_segments, separate_components
import base64
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class edi_envelope(models.Model):
    _inherit = 'edi.envelope'
    
    def _envelope_type(self):
        return super(edi_envelope, self)._envelope_type() + [('edifact', 'EDIFACT')]

    @api.one
    def split(self):
        if self.envelope_type == 'edifact':
            message = None
            #_logger.warn('body: %s' % base64.b64decode(self.body))
            msg_count = 0
            orders = []
            for segment in separate_segments(base64.b64decode(self.body)):
                segment = separate_components(segment)
                if segment[0] == 'UNB':
                    sender = self._get_partner(segment[2])
                    recipient = self._get_partner(segment[3])
                    date = segment[4][0]
                    time = segment[4][1]
                elif segment[0] == 'UNH':
                    edi_type = self._get_edi_type(segment)
                    message = [segment]
                    segment_count = 1
                elif segment[0] == 'UNT':
                    #skapa message
                    if segment_count + 1 != int(segment[1]):
                        raise Warning('Wrong number of segments! %s %s' % (segment_count, segment))
                    message.append(segment)
                    orders.append({
                        'name': 'foobar',
                        'envelope_id': self.id,
                        'body': base64.b64encode(str(message)),
                        'edi_type': edi_type,
                        'consignor_id': sender.id,
                        'consignee_id': recipient.id,
                    })
                    message = None
                    msg_count += 1
                elif message:
                    message.append(segment)
                    segment_count += 1
                elif segment[0] == 'UNZ':
                    if msg_count != int(segment[1]):
                        raise Warning('Wrong message count!')
            
            for order_dict in orders:
                self.env['edi.message'].create(order_dict)
        
        super(edi_envelope, self).split()

    def _get_partner(self, l):
        _logger.warn('get partner %s' % l)
        if l[1] == '14':
            partner = self.env['res.partner'].search([('gln', '=', l[0])])
            _logger.warn(partner)
            if len(partner) == 1:
                return partner
            _logger.warn('Warning!')
            raise Warning("Unknown part %s" % len(l) >0 and l[0] or "[EMPTY LIST!]")
    
    def _get_edi_type(self, segment):
        if segment[2][0] == 'ORDERS':
            return 'orders'
    
class edi_message(models.Model):
    _inherit='edi.message'
    
    def _edi_type(self):
        return super(edi_message, self)._edi_type() + [('orders', 'ORDERS')]
    
    @api.one
    def unpack(self):
        if self.edi_type == 'orders':
            segment_count = 0
            delivery_dt = None
            #Delivered by?
            delivery_prom_dt = None
            #Message sent date?
            doc_dt = None
            order_values = {}
            order_values['order_line'] = []
            line = {}
            for segment in eval(base64.b64decode(self.body)):
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
                    line['product_uom_qty'] = self._parse_quantity(segment[1])
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
                        raise Warning('Wrong number of segments! %s %s' % (segment_count, segment))
                    #Add last line
                    if line:
                        order_values['order_line'].append((0, 0, line))
                    _logger.warn(order_values)
                    #create order
                    self.env['sale.order'].create(order_values)
    
    def _get_partner(self, l):
        _logger.warn('get partner %s' % l)
        partner = None
        if l[2] == '9':
            partner = self.env['res.partner'].search([('gln', '=', l[0])])
        _logger.warn(partner)
        if len(partner) == 1:
            return partner[0]
        _logger.warn('Warning!')
        raise Warning("Unknown part %s" % len(l) >0 and l[0] or "[EMPTY LIST!]")
    
    def _parse_quantity(self, l):
        #if l[0] == '21':
        return float(l[1])
    
    def _get_product(self, l):
        product = None
        if l[1] == 'EN':
            product = self.env['product.product'].search([('default_code', '=', l[0])])
        if product:
            return product
        raise Warning('Product not found! EAN: %s' % l[0])
    
    @api.model
    def _parse_date(self, l):
        if l[2] == '102':
            return fields.Datetime.to_string(datetime.strptime(l[1], '%Y%m%d'))        
    
#~ class edi_route(models.Model):
    #~ _inherit = 'edi.route'
    


# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
