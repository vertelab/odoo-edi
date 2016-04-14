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
                    edi_type = segment[2][0]
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
  
#~ class edi_route(models.Model):
    #~ _inherit = 'edi.route'
    


# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
