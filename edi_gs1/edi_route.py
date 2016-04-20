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

class edi_envelope(models.Model):
    _inherit = 'edi.envelope' 
    
    @api.one
    def fold(self,route): # Folds messages in an envelope
        for m in self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',route.id)]):
            m.envelope_id = self.id
        envelope = super(edi_envelope,self).fold(route)
        if route.envelope_type == 'edifact':
            interchange_controle_ref = ''
            date = ''
            time = ''
            UNA = "UNA:+.? '"
            UNB = "UNB+UNOC:3+%s:14+%s:14+%s:%s+%s++ICARSP4'" % (route.partner_id.company_id.partner_id.gs1_gln, route.partner_id.gs1_gln, date, time, interchange_control_ref)
            body = ''.join([base64.b64decode(m.body) for m in envelope.message_ids])
            UNZ = "UNZ+%s+627'" % (len(envelope.message_ids),len(body))
            envelope.body = base64.b64encode(UNA + UNB + body + UNZ)
        return envelope

    def _create_UNB_segment(self,sender, recipient):
        self._seg_count += 1
        return "UNB+UNOC:3+%s:14+%s:14+%s:%s+%s++ICARSP4'" % (sender.gs1_gln, recipient.gs1_gln, date, time, interchange_control_ref)


class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    edi_type = fields.Selection(selection_add=[('ORDERS','ORDERS'),('ORDRSP','ORDRSP')])
    envelope_type = fields.Selection(selection_add=[('edifact','Edifact')])


def _escape_string(s):
    if isinstance(s, basestring):
        return s.replace('?', '??').replace('+', '?+').replace(':', '?:').replace("'", "?'") #.replace('\n', '') needed?
    return s



class edi_message(models.Model):
    _inherit='edi.message'



    _seg_count = 0

    def UNH(self,edi_type=False, version='D', release='96A'):
        self._seg_count += 1
        if not edi_type:
            edi_type = self.edi_type
        return "UNH+{ref_no}+{msg_type}:{version}:{release}:UN:EDIT30'".format(ref_no=self.name,msg_type=edi_type,version=version,release=release)

    def BGM(self,doc_code=False, doc_no=False,status=False):
        # Beginning of message
        # doc_code = Order, Document/message by means of which a buyer initiates a transaction with a seller involving the supply of goods or services as specified, according to conditions set out in an offer, or otherwise known to the buyer.
        # BGM+220::9+20120215150105472'
        # doc_code 231 Purchase order response, Response to an purchase order already received.
        # BGM+231::9+201101311720471+4'
        # doc_code 351 Despatch advice, Document/message by means of which the seller or consignor informs the consignee about the despatch of goods.
        # BGM+351+SO069412+9'
        self._seg_count += 1
        if doc_code == 231: # Resp agency = EAN/GS1 (9), Message function code = Change (4)
            return "BGM+231::9+{doc_no}+4'".format(doc_no=_escape_string(doc_no))    
        elif doc_code == 220: # Resp agency = EAN/GS1 (9),
            return "BGM+220::9+{doc_no}'".format(doc_no=_escape_string(doc_no))
        elif doc_code == 351:
            return "BGM+351+{doc_no}+9'".format(doc_no=_escape_string(doc_no))
            

    def DTM(self,func_code=False, dt=False, format=102):
        self._seg_count += 1
        # 132 =  Transport means arrival date/time, estimated
        # 137 =  Document/message date/time, date/time when a document/message is issued. This may include authentication.
        if not dt:
            dt = fields.Datetime.from_string(fields.Datetime.now())
        if format == 102:
            dt = fields.Datetime.from_string(dt).strftime('%Y%M%d')
        elif format == 203:
            dt = fields.Datetime.from_string(dt).strftime('%Y%M%d%H%M')
        return "DTM+%s:%s:%s'" % (func_code, dt, format)

    def _create_FTX_segment(self,msg1, msg2='', msg3='', msg4='', msg5='', subj='ZZZ', func=1, ref='001'):
        self._seg_count += 1        
        return "FTX+%s+%s+%s+%s:%s:%s:%s:%s'" % (subj, func, ref, _escape_string(msg1), _escape_string(msg2), _escape_string(msg3), _escape_string(msg4), _escape_string(msg5))

    #CR = Customer Reference
    def RFF(self,ref, qualifier='CR'):
        # CR = Customer reference, AAS = Transport document number, Reference assigned by the carrier or his agent to the transport document.
        self._seg_count += 1
        return "RFF+%s:%s'" % (qualifier, ref)

    def _NAD(self,role, partner, type='GLN'):
        self._seg_count += 1        
        if type == 'GLN':
            party_id = partner.gs1_gln
            if not party_id:
                #raise Warning('NAD missing GLN role=%s partner=%s' % (role,partner.name))
                party_id = 1 # Jusr for test
            code = 9
        return "NAD+%s+%s::%s'" % (role, party_id, code)
    def NAD_SU(self,type='GLN'):
        return self._NAD('SU',self.consignor_id,type)
    def NAD_BY(self,type='GLN'):
        return self._NAD('BY',self.consignee_id,type)
    def NAD_SH(self,type='GLN'):
        return self._NAD('SH',self.forwarder_id,type)
    def NAD_DP(self,type='GLN'):
        return sielf._NAD('DP',self.carrier_id,type)

    #code = error/status code
    def LIN(self,nr, line):
        self._seg_count += 1        
        if line.product_uom_qty <= 0:
            code = 7 # Not accepted
        elif line.product_uom_qty != line.order_qty:
            code = 12 # Quantity changed
        else:
            code = 5 # Accepted without amendment
        return "LIN+%s+%s+%s:%s'" %(nr, code, line.product_id.gs1_gtin14, 'EN')

    #SA = supplier code BP = buyer code
    def PIA(self,product, code):
        self._seg_count += 1
        prod_nr = None
        if code == 'SA':
            prod_nr = product.default_code
        elif code == 'BP':
            pass
        if prod_nr:
            return "PIA+5+%s:%s'" % (prod_nr, code)
        return ""

    def QTY(self,line):
        self._seg_count += 1
        #~ if line.product_uom_qty != line.order_qty:
            #~ code = 12
        #~ else:
        code = 21
        return "QTY+%s:%s'" % (code, line.product_uom_qty)

    def UNS(self):
        return "UNS+S'"

    def UNT(self):
        return "UNT+{count}+{ref}'".format(count=self._seg_count,ref=self.name)

            
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
            product = self.env['product.product'].search([('gs1_gtin14', '=', l[0])])
        if product:
            return product
        raise Warning('Product not found! EAN: %s' % l[0])
    
    @api.model
    def _parse_date(self, l):
        if l[2] == '102':
            return fields.Datetime.to_string(datetime.strptime(l[1], '%Y%m%d'))        

