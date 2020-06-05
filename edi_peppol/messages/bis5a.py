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
from odoo import models, fields, api, _
import base64
from datetime import datetime
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)


class edi_message(models.Model):
    _inherit='edi.message'
    _edi_lines_tot_qty = 0
    
    @api.one
    def pack(self):
        super(edi_message, self).pack()
        if self.edi_type.id == self.env.ref('edi_peppol.edi_message_type_bis5a').id:
            if self.model_record._name != 'account.invoice':
                raise Warning("INVOIC: Attached record is not an account.invoice! {model}".format(model=self.model_record._name))
            invoice = self.model_record
            msg = self.UNH(self.edi_type.name)
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

