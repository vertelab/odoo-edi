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
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_contrl').id:
            _logger.warn('model_record: %s' % self.model_record)
            if self.model_record._name != 'edi.envelope':
                raise Warning("CONTRL: Attached record is not an edi.envelope!")
            envelope = self.model_record
            msg =  self.UNH(edi_type='CONTRL', ass_code='EAN002')
            msg += self.UCI(envelope.ref, envelope.sender, envelope.recipient)
            msg += self.UNS()
            msg += self.UNT()
            
            #TODO: What encoding should be used?
            self.body = base64.b64encode(self._gs1_encode_msg(msg))
        super(edi_message, self)._pack()

    @api.one
    def _unpack(self):
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_contrl').id:
            segment_count = 0
            for segment in self._gs1_get_components():
                segment_count += 1
                _logger.warn('segment: %s' % segment)
                
                if segment[0] == 'UCI':
                    envelope = self.env['edi.envelope']
                    sender = envelope._get_partner(segment[2], 'sender')
                    recipient = envelope._get_partner(segment[3], 'recipient')
                    envelope = self._find_envelope(segment[1], sender, recipient)
                    self.model = envelope._name
                    self.res_id = envelope.id
                elif segment[0] == 'UNT':
                    if segment_count != int(segment[1]):
                        raise TypeError('Wrong number of segments! %s %s' % (segment_count, segment),segment)
        else:
            super(edi_message, self)._unpack()

#Example CONTRL message creation.
#~ if envelope.sender.id == 4002 and envelope.application != 'CONTRL':
    #~ msg = env['edi.message'].create({
        #~ 'edi_type': envelope._get_edi_type_id('CONTRL'),
        #~ 'sender': envelope.recipient.id,
        #~ 'recipient': envelope.sender.id,
        #~ 'route_type': env.route_id.route_type,
        #~ 'route_id': env.route_id.id,
        #~ 'model': 'edi.envelope',
        #~ 'res_id': envelope.id,
    #~ })

class edi_envelope(models.Model):
    _inherit = 'edi.envelope'
    
    @api.one
    def envelope_opened(self):
        if self.route_id and self.route_id.route_type == 'esap20':
            self.route_id.edi_action('edi.envelope.envelope_opened', envelope=self)
        super(edi_envelope, self).envelope_opened()
