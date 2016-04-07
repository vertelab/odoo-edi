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
    
    @api.model
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
            buyer = None
            for segment in eval(base64.b64decode(self.body)):
                segment_count += 1
                _logger.warn('segment: %s' % segment)
                #Begin Message
                if segment[0] == 'BGM':
                    self.name = segment[2]
                #Datetime
                elif segment[0] == 'DTM':
                    function = segment[0]
                    dt = segment[1]
                    dt_format = segment[2]
                    if function == '2':
                        delivery_dt = _parse_date(dt, dt_format)
                    elif function == '69':
                        delivery_prom_dt = _parse_date(dt, dt_format)
                    elif function == '137':
                        doc_dt = _parse_date(dt, dt_format)
                elif segment[0] == 'NAD':
                    if segment[1] == 'BY':
                        buyer = self.env['edi.envelope']._get_partner(segment[2])
                    elif segment[1] == 'SU':
                        supplier = self.env['edi.envelope']._get_partner(segment[2])
                    elif segment[1] == 'SN':
                        store_keeper = self.env['edi.envelope']._get_partner(segment[2])
                    elif segment[1] == 'CN':
                        consignee = self.env['edi.envelope']._get_partner(segment[2])
                    #Delivery Party
                    elif segment[1] == 'DP':
                        recipient = self.env['edi.envelope']._get_partner(segment[2])
                elif segment[0] == 'LIN':
                    pass
                elif segment[0] == 'QTY':
                    pass
                elif segment[0] == 'PIA':
                    pass
                elif segment[0] == 'FTX':
                    pass
                elif segment[0] == 'RFF':
                    #CR customer reference number
                    #GN Government Reference Number
                    #VA VAT registration number
                    pass
                elif segment[0] == '':
                    pass
                #End of message
                elif segment[0] == 'UNT':
                    if segment_count != int(segment[1]):
                        raise Warning('Wrong number of segments! %s %s' % (segment_count, segment))
                    #create order
    
    def _parse_date(self, dt, dt_format):
        if dt_format == '102':
            return fields.Datetime.to_string(datetime.strptime(dt, '%Y%m%d'))        
    
class edi_route(models.Model):
    _inherit = 'edi.route'
    
class res_partner(models.Model):
    _inherit='res.partner'
    
    gln = fields.Char(string="Global Location Number",help="Global Location Number (GLN)")

# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
