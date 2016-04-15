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

def _escape_string(s):
    if isinstance(s, basestring):
        return s.replace('?', '??').replace('+', '?+').replace(':', '?:').replace("'", "?'") #.replace('\n', '') needed?
    return s

def _get_nad_ref_from_partner(partner, type):
    if type == 'GLN':
        return partner.gs1_gln, 9

#move to route
def _create_UNB_segment(sender, recipient):
    return "UNB+UNOC:3+%s:14+%s:14+%s:%s+%s++ICARSP4'" % (sender.gs1_gln, recipient.gs1_gln, date, time, interchange_control_ref)

def _create_UNH_segment(msg_type, ref_no_repeat_in_unt, version='D', release='96A'):
    return "UNH+%s+%s:%s:%s:UN:EDIT30'" % (ref_no_repeat_in_unt, msg_type, version, release)

def _create_BGM_segment(doc_name, doc_no, msg_function, resp_agency=9):
    return "BGM+%s::%s+%s+%s'" % (doc_name, resp_agency, doc_no, msg_function)

def _parse_dt_DTM(dt, format):
    if format == 102:
        return dt.strftime('%Y%M%d')
    elif format == 203:
        return dt.strftime('%Y%M%d%H%M')

def _create_DTM_segment(func_code, dt, format=102):
    return "DTM+%s:%s:%s'" % (func_code, _parse_dt_DTM(dt,format), format)

def _create_FTX_segment(msg1, msg2='', msg3='', msg4='', msg5='', subj='ZZZ', func=1, ref='001'):
    return "FTX+%s+%s+%s+%s:%s:%s:%s:%s'" % (subj, func, ref, _escape_string(msg1), _escape_string(msg2), _escape_string(msg3), _escape_string(msg4), _escape_string(msg5))

#CR = Customer Reference
def _create_RFF_segment(ref, qualifier='CR'):
    return "RFF+%s:%s'" % (qualifier, ref)

def _create_NAD_segment(role, partner, type='GLN'):
    party_id, code = _get_nad_ref_from_partner(partner, type)
    return "NAD+%s+%s::%s'" % (role, party_id, code)

#code = error/status code
def _create_LIN_segment(nr, line):
    if line.product_uom_qty <= 0:
        code = 7 # Not accepted
    elif line.product_uom_qty != line.order_qty:
        code = 12 # Quantity changed
    else:
        code = 5 # Accepted without amendment
    return "LIN+%s+%s+%s:%s'" %(nr, code, line.product_id.gs1_gtin14, 'EN')

#SA = supplier code BP = buyer code
def _create_PIA_segment(product, code):
    prod_nr = None
    if code == 'SA':
        prod_nr = product.default_code
    elif code == 'BP':
        pass
    if prod_nr:
        return "PIA+5+%s:%s'" % (prod_nr, code)
    return ""

def _create_QTY_segment(line):
    #~ if line.product_uom_qty != line.order_qty:
        #~ code = 12
    #~ else:
    code = 21
    return "QTY+%s:%s'" % (code, line.product_uom_qty)

def _create_UNS_segment():
    return "UNS+S'"

def _create_UNT_segment(segment_count, ref):
    return "UNT+%s+%s'" % (segment_count, ref)

def _check_order_status(order):
    edited = 0
    zeroed = 0
    for line in order.order_line:
        if line.product_uom_qty == 0:
            zeroed += 1
        if line.product_uom_qty != line.order_qty:
            edited += 1
    if zeroed == len(order.order_line):
        return 27
    elif edited + zeroed > 0:
        return 4
    return 0 #TODO: find correct code



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
UNH				EDIFACT-styrinformation.
BGM				Typ av Ordersvar.
DTM		Bekräftat leveransdatum.
FTX	Uppgifter för felanalys
RFF- DTM	Referensnummer				
NAD		Köparens identitet (EAN lokaliseringsnummer).
		Leverantörens identitet (EAN lokaliseringsnummer).

LIN		Radnummer.
			EAN artikelnummer.
PIA		Kompletterande artikelnummer.
QTY	Kvantitet.

UNS		Avslutar orderrad.
UNT		Avslutar ordermeddelandet.
""" 

    #TODO: replace with new selection_add (?) parameter
    def _edi_type(self):
        return super(edi_message, self)._edi_type() + [('orders', 'ORDERS')]
    
    @api.one
    def tmp_ordererkannande(self):
        """
UNA 		C 		1 		SERVICE STRING ADVICE
UNB 		M 		1 		INTERCHANGE HEADER
UNH 		M 		1 		MESSAGE HEADER
BGM 		M 		1 		Document type and number
DTM 		M 		35 		Order response date
DTM 		M 		35 		Order response date time
FTX 		C 		99 		Reason for rejection
RFF 		M 		1 		Reference to order
NAD 		M 		1 		Supplier
NAD 		M 		1 		Buyer
UNS 		M 		1 		SECTION CONTROL
UNT 		M 		1 		MESSAGE TRAILER
UNZ 		M 		1 		INTERCHANGE TRAILER
"""
        if self.edi_type == 'ORDRSP':
            if not self.model_record:
                raise Warning("ORDRSP: Can not create message without attached sale.order record!")
            elif self.model_record._model != 'sale.order':
                raise Warning("ORDRSP: Attached record is not a sale.order!")
            ref = self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_message').id)
            msg = _create_UNH_segment('ORDRSP', ref)
            msg += _create_BGM_segment(231, _escape_string(self.model_record.name), 12)
            dt = fields.Datetime.from_string(fields.Datetime.now())
            msg += _create_DTM_segment(137, dt)
            msg += _create_DTM_segment(137, dt, 203)
            msg += _create_FTX_segment('')
            msg += _create_RFF_segment(order.client_order_ref)
            msg += _create_NAD_segment('BY', order.partner_id)
            msg += _create_NAD_segment('SU', self.env.ref('base.main_partner'))
            msg += _create_UNS_segment()
            msg += _create_UNT_segment(10, ref)
            self.body = base64.b64encode(msg)
    
    @api.one
    def pack(self):
        if self.edi_type == 'ORDRSP':
            if not self.model_record:
                raise Warning("ORDRSP: Can not create message without attached sale.order record!")
            elif self.model_record._model != 'sale.order':
                raise Warning("ORDRSP: Attached record is not a sale.order!")
            status = _check_order_status(self.model_record)
            if status != 0:
                ref = self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_message').id)
                msg = _create_UNH_segment('ORDRSP', ref)
                msg += _create_BGM_segment(231, self.model_record, status)
                dt = fields.Datetime.from_string(fields.Datetime.now())
                msg += _create_DTM_segment(137, dt)
                #Another DTM?
                #FNX?
                msg += _create_RFF_segment(order.client_order_ref)
                msg += _create_NAD_segment('BY', order.partner_id)
                msg += _create_NAD_segment('SU', self.env.ref('base.main_partner'))
                line_index = 0
                for line in order_line:
                    line_index += 1
                    msg += _create_LIN_segment(line_index, line)
                    msg += _create_PIA_segment(line.product_id, 'SA')
                    #Required?
                    #msg += _create_PIA_segment(line.product_id, 'BP')
                    msg += _create_QTY_segment(line)
                msg += _create_UNS_segment()
                msg += _create_UNT_segment(8 + 3 * line_index, ref)
                self.body = base64.b64encode(msg)
    @api.one
    def unpack(self):
        if self.edi_type == 'ORDERS':
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
                        raise Warning('Wrong number of segments! %s %s' % (segment_count, segment))
                    #Add last line
                    if line:
                        order_values['order_line'].append((0, 0, line))
                    _logger.warn(order_values)
                    #create order
                    order = self.env['sale.order'].create(order_values)
                    self.model = order._name
                    self.res_id = order.id
    
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

#TODO: move to another module
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    order_qty = fields.Float(string='Original Order Quantity')

class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.one
    def tmp_ordererkannande(self):
        _logger.warn('tmp_ordererkännande')
        self._edi_message_create('ORDRSP')
