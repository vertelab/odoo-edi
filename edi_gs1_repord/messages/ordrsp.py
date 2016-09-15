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
            errors = []
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
                        order = self.env['rep.order'].search([('client_order_ref', '=', segment[2])])[0]
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
                    errors.append(sys.exc_info())
            
            res = 'status: ' + order_state
            res += '\ndelivery date: ' + delivery_date
            res += '\nmessage: ' + text
            if lines:
                res += '\n' 
                for line in lines:
                    res += '\nline %s:\n\tproduct: %s\n\tquantity: %s\n\tstatus: %s\n' % (
                        line.get('sequence', ''), line.get('product', 'not found'),
                        line.get('quantity', ''),
                        'Not accepted' if line.get('status', '') == '7' else line.get('status', 'Unknown'))
            res += '\n\noriginal message:\n' + msg
            
            if errors:
                errors.reverse()
                self.route_id.log("%s error(s) when reading ORDRSP '%s'.\n%s" % (len(errors), self.name, res), errors)
                self.state = 'canceled'
            else:
                user = self.env['res.users'].browse(self._uid)
                self.env['mail.message'].create({
                    'body': res,
                    'subject': 'Order response received',
                    'author_id': user.partner_id.id,
                    'res_id': order.id,
                    'model': order._name,
                    'type': 'comment',
                })
        else:
            super(edi_message, self)._unpack()
