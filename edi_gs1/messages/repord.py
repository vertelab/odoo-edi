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
    
    edi_type = fields.Selection(selection_add=[('REPORD','REPORD')])
        
    """
UNH+204853+DESADV:D:93A:UN:EDIT30'
BGM+351+SO069412+9'
DTM+137:20120314:102'
DTM+132:20120315:102'
RFF+AAS:229933'
NAD+BY+7301005230007::9'
NAD+SH+7350059980017::9'
NAD+DP+7301005230007::9'
CPS+1+1'
PAC+1++34'
PCI+30E'
GIN+SS+373500310002299334'
LIN+1'
RFF+CR:039893091'
LOC+83+7301005230007::9'
LOC+7+7301004113585::9:63710'
DTM+2:20120316:102'
CPS+1+1'
PAC+1++34'
PCI+30E'
GIN+SS+373500310002299341'
LIN+1'
RFF+CR:039893091'
LOC+83+7301005230007::9'
LOC+7+7301004113585::9:63710'
DTM+2:20120316:102'
UNT+27+204853'
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
        return [t for t in super(edi_message, self)._edi_type() + [('REPORD','REPORD')] if not t[0] == 'none']
    
    @api.one
    def _pack(self):
        super(edi_message, self)._pack()
        if self.edi_type == 'REPORD':
            if self.model_record._name != 'sale.order':
                raise ValueError("DESADV: Attached record is not a sale.order! {model}".format(model=self.model_record._name),self.model_record._name)
            status = _check_order_status(self.model_record)
            if status != 0:
                msg = self.UNH('ORDERS')
                msg += self.BGM(231, self.model_record.name, status)
                dt = fields.Datetime.from_string(fields.Datetime.now())
                msg += self._create_DTM_segment(137, dt)
                #Another DTM?
                #FNX?
                msg += self._create_RFF_segment(self.model_record.client_order_ref)
                msg += self.NAD_BY()
                msg += self.NAD_SU()
                line_index = 0
                for line in self.model_record.order_line:
                    line_index += 1
                    msg += self._create_LIN_segment(line_index, line)
                    msg += self._create_PIA_segment(line.product_id, 'SA')
                    msg += self._create_PIA_segment(line.product_id, 'BP', self.model_record.partner_id)
                    msg += self._create_QTY_segment(line)
                msg += self.UNS()
                msg += self.UNT()
                self.body = base64.b64encode(msg)
