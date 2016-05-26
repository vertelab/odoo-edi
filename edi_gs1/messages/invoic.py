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
    edi_type = fields.Selection(selection_add = [('INVOIC','INVOIC')])
    
    _edi_lines_tot_qty = 0
    
    @api.one
    def _pack(self):
        super(edi_message, self)._pack()
        if self.edi_type == 'INVOIC':
            if self.model_record._name != 'account.invoice':
                raise ValueError("INVOIC: Attached record is not an account.invoice! {model}".format(model=self.model_record._name),self.model_record._name)
            invoice = self.model_record
            msg = self.UNH(self.edi_type)
            #280 = 	Commercial invoice - Document/message claiming payment for goods or services supplied under conditions agreed between seller and buyer.
            #9 = Original - Initial transmission related to a given transaction.
            _logger.warn(invoice.name)
            msg += self.BGM(280, invoice.name, 9)
            
            #Dates
            #Document date
            msg += self.DTM(137)
            #Actual delivery date
            #msg += self.DTM(35)
            #Despatch date
            #msg += self.DTM(11)
            #Invoice period
            #msg += self.DTM(167)
            #msg += self.DTM(168, invoice.date_due)
            
            #Invoice reference
            msg += self.RFF(invoice.name, 'IV')
            #Order reference
            msg += self.RFF(invoice.origin, 'ON')
            msg += self.NAD_SU()
            _logger.warn(self.consignor_id.name)
            msg += self.RFF(self.consignor_id.vat, 'VA')
            _logger.warn('consignor: %s' % self.consignee_id.company_registry)
            msg += self.RFF(self.consignor_id.company_registry, 'GN')
            msg += self.NAD_BY()
            msg += self.RFF(self.consignee_id.vat, 'VA')
            msg += self.NAD_CN()
            #CUX Currency
            msg += self.PAT()
            msg += self.DTM(13, invoice.date_due)
            
            #Shipping charge, discount, collection reduction, service charge, packing charge 
            #   ALC Freigt charge
            #   MOA Ammount
            #   TAX
            
            for line in invoice.invoice_line:
                self._edi_lines_tot_qty += line.quantity
                msg += self.LIN(line)
                msg += self.PIA(line.product_id, 'SA')
                #Invoice qty
                msg += self.QTY(line)
                #Delivered qty
                #msg += self._create_QTY_segment(line)
                #Reason for crediting
                #ALI
                msg += self.MOA(line.price_subtotal)
                #Net unit price, and many more
                #PRI
                #Reference to invoice. Again?
                #RFF
                #Justification for tax exemption
                #TAX
            msg += self.UNS()
            msg += self.CNT(1, self._edi_lines_tot_qty)
            msg += self.CNT(2, self._lin_count)
            #Amount due
            msg += self.MOA(invoice.amount_total, 9)
            #Small change roundoff
            #self.msg += self.MOA()
            #Sum of all line items
            msg += self.MOA(invoice.amount_total, 79)
            #Total taxable amount
            msg += self.MOA(invoice.amount_untaxed, 125)
            #Total taxes
            msg += self.MOA(invoice.amount_tax, 176)
            #Total allowance/charge amount
            #self.msg += self.MOA(, 131)
            #TAX-MOA-MOA
            #self.msg += self.TAX()
            #self.msg += self.MOA()
            #self.msg += self.MOA()
            #Tax subtotals
            msg += self.TAX('%.2f' % (invoice.amount_tax / invoice.amount_total))
            msg += self.MOA(invoice.amount_tax, 150)
            msg += self.UNT()
            self.body = base64.b64encode(msg.encode('utf-8'))

