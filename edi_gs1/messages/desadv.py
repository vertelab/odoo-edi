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
    edi_type = fields.Selection(selection_add=[('DESADV','DESADV')])  


class edi_message(models.Model):
    _inherit='edi.message'
        
    """
UNH+204853+DESADV:D:93A:UN:EDIT30'
BGM+351+SO069412+9'
BGM+231::9+201101311720471+4'
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
    edi_type = fields.Selection(selection_add=[('DESADV','DESADV')])  
    
    @api.one
    def pack(self):
        super(edi_message, self).pack()
        if self.edi_type == 'DESADV':
            if self.model_record._name != 'stock.pack':
                raise Warning("DESADV: Attached record is not a stock.pack! {model}".format(model=self.model_record._name))

            msg = self.UNH('DESADV')
            msg += self.BGM(doc_code=351, doc_no=self.model_record.name)
            msg += self.DTM(137)
            msg += self.DTM(132,dt=self.model_record.date)
            #Another DTM?
            #FNX?
            msg += self.RFF(self.model_record.client_order_ref,qualifier='AAS')
            msg += self.NAD_BY()
            msg += self.NAD_SH()
            msg += self.NAD_DP()
            
                    #~ 'EANSENDER':        order_record['EANRECEIVER'],
                    #~ 'EANRECEIVER':      order_record['EANSENDER'],
					#~ 'TEST':             '0',
					#~ 'DESADVNUMBER':		order_record['name'],	
					#~ 'DESADVDATE':	    datetime.datetime.strptime(order_record['date_order'],'%Y-%m-%d').strftime("%Y%m%d"),
					#~ 'ESTDELDATE':	    datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
					#~ 'EANBUYER':	        '7301005140009',
					#~ 'EANSHIPPER':	    '7350031550009',    
					#~ 'EANDELIVERY':	    partner['consignee_iln'],	

            
            line_index = 0
            for line in self.model_record.order_line:
                line_index += 1
                msg += self.LIN(line_index, line)
                msg += self.PIA(line.product_id, 'SA')
                #Required?
                #msg += self._create_PIA_segment(line.product_id, 'BP')
                msg += self.QTY(line)
            msg += self.UNS()
            msg += self.UNT()
            self.body = base64.b64encode(msg)
