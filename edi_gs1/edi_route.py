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



class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    def _edi_type(self):
        return [t for t in super(edi_route, self)._edi_type() + [('ORDERS','ORDERS'),('ORDRSP','ORDRSP')] if not t[0] == 'none']


def _escape_string(s):
    if isinstance(s, basestring):
        return s.replace('?', '??').replace('+', '?+').replace(':', '?:').replace("'", "?'") #.replace('\n', '') needed?
    return s



class edi_message(models.Model):
    _inherit='edi.message'

    #move to route
    def _create_UNB_segment(self,sender, recipient):
        return "UNB+UNOC:3+%s:14+%s:14+%s:%s+%s++ICARSP4'" % (sender.gs1_gln, recipient.gs1_gln, date, time, interchange_control_ref)

    def UNH(self,msg_type, version='D', release='96A'):
        return "UNH+{ref_no}+{msg_type}:{version}:{release}:UN:EDIT30'".format(ref_no=self.name,msg_type=msg_type,version=version,release=release)

    def BGM(self,doc_name, doc_no, msg_function, resp_agency=9):
        return "BGM+{doc_name}::{resp_agency}+{doc_no}+{msg_function}'".format(doc_name=doc_name,resp_agency=resp_agency,doc_no=_escape_string(doc_no),msg_function=msg_function)

    def _create_DTM_segment(self,func_code, dt=False, format=102):
        if not dt:
            dt = fields.Datetime.from_string(fields.Datetime.now())
        if format == 102:
            dt = dt.strftime('%Y%M%d')
        elif format == 203:
            dt = dt.strftime('%Y%M%d%H%M')
        return "DTM+%s:%s:%s'" % (func_code, dt, format)

    def _create_FTX_segment(self,msg1, msg2='', msg3='', msg4='', msg5='', subj='ZZZ', func=1, ref='001'):
        return "FTX+%s+%s+%s+%s:%s:%s:%s:%s'" % (subj, func, ref, _escape_string(msg1), _escape_string(msg2), _escape_string(msg3), _escape_string(msg4), _escape_string(msg5))

    #CR = Customer Reference
    def _create_RFF_segment(self,ref, qualifier='CR'):
        return "RFF+%s:%s'" % (qualifier, ref)

    def _create_NAD_segment(self,role, partner, type='GLN'):
        if type == 'GLN':
            party_id = partner.gs1_gln
            code = 9
        return "NAD+%s+%s::%s'" % (role, party_id, code)

    #code = error/status code
    def _create_LIN_segment(self,nr, line):
        if line.product_uom_qty <= 0:
            code = 7 # Not accepted
        elif line.product_uom_qty != line.order_qty:
            code = 12 # Quantity changed
        else:
            code = 5 # Accepted without amendment
        return "LIN+%s+%s+%s:%s'" %(nr, code, line.product_id.gs1_gtin14, 'EN')

    #SA = supplier code BP = buyer code
    def _create_PIA_segment(self,product, code):
        prod_nr = None
        if code == 'SA':
            prod_nr = product.default_code
        elif code == 'BP':
            pass
        if prod_nr:
            return "PIA+5+%s:%s'" % (prod_nr, code)
        return ""

    def _create_QTY_segment(self,line):
        #~ if line.product_uom_qty != line.order_qty:
            #~ code = 12
        #~ else:
        code = 21
        return "QTY+%s:%s'" % (code, line.product_uom_qty)

    def _create_UNS_segment(self):
        return "UNS+S'"

    def _create_UNT_segment(self,segment_count, ref):
        return "UNT+%s+%s'" % (segment_count, ref)

            
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

