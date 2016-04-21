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
    edi_type = fields.Selection(selection_add=[('INVOIC','INVOIC')]) 

class edi_message(models.Model):
    _inherit='edi.message'
        
    """
UNH+272+INVOIC:D:93A:UN:EDIT30'
BGM+380+2010/024'
DTM+50:20101201:102'
DTM+35:20101119:102'
RFF+CS:ICA'
NAD+BY+7301005140009::9'
NAD+CN+7301005140009::9'
NAD+SU+7300009025411::9'
RFF+VA:SE556208469801'
RFF+GN:556208-4698'
PAT+3++6'
DTM+13:20100101:102'
ALC+C++2++IS'
MOA+23:17314.91'
LIN+10++27318690055642:EN'
PIA+5+253387:SA'
QTY+47:147:PCE'
MOA+203:9702.00'
PRI+AAB:66.00'
TAX+7+VAT+++:::0.00+S'
LIN+20++27318690055499:EN'
PIA+5+2533545:SA'
QTY+47:9:PCE'
MOA+203:489.96'
PRI+AAB:54.44'
TAX+7+VAT+++:::0.00+S'
LIN+30++27318690055192:EN'
PIA+5+2533560:SA'
QTY+47:9:PCE'
MOA+203:489.96'
PRI+AAB:54.44'
TAX+7+VAT+++:::0.00+S'
LIN+40++27318690055901:EN'
PIA+5+253388:SA'
QTY+47:19:PCE'
MOA+203:1449.32'
PRI+AAB:76.28'
TAX+7+VAT+++:::0.00+S'
LIN+50++27318690055666:EN'
PIA+5+253389:SA'
QTY+47:20:PCE'
MOA+203:1490.40'
PRI+AAB:74.52'
TAX+7+VAT+++:::0.00+S'
LIN+60++27318690055659:EN'
PIA+5+253390:SA'
QTY+47:21:PCE'
MOA+203:1496.88'
PRI+AAB:71.28'
TAX+7+VAT+++:::0.00+S'
UNS+S'
CNT+2:6'
MOA+9:17314.91'
MOA+79:15118.52'
MOA+125:15118.52'
MOA+176:2196.39'
TAX+7+VAT+++:::12.0+S'
MOA+176:2196.39'
UNT+59+272'
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
        return [t for t in super(edi_message, self)._edi_type() + [('INVOIC','INVOIC')] if not t[0] == 'none']
            
    @api.one
    def pack(self):
        super(edi_message, self).pack()
        if self.edi_type == 'INVOIC':
            if self.model_record._name != 'account.invoic':
                raise Warning("INVOIC: Attached record is not a sale.order! {model}".format(model=self.model_record._name))
            status = _check_order_status(self.model_record)
            if status != 0:
                msg = self.UNH(self.edi_type)
                msg += self.BGM(231, self.model_record.name, status)
                dt = fields.Datetime.from_string(fields.Datetime.now())
                msg += self._create_DTM_segment(137, dt)
                #Another DTM?
                #FNX?
                msg += self._create_RFF_segment(self.model_record.client_order_ref)
                msg += self.NAD_BY()
                msg += self.NAD_CN()
                msg += self.NAD_SU()
                line_index = 0
                for line in self.model_record.order_line:
                    line_index += 1
                    msg += self._create_LIN_segment(line_index, line)
                    msg += self._create_PIA_segment(line.product_id, 'SA')
                    #Required?
                    #msg += self._create_PIA_segment(line.product_id, 'BP')
                    msg += self._create_QTY_segment(line)
                msg += self.UNS()
                msg += self.UNT()
                self.body = base64.b64encode(msg)

