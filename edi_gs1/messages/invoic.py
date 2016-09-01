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
from openerp.exceptions import except_orm, Warning, RedirectWarning
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
UNH             EDIFACT-styrinformation.
BGM             Typ av Ordersvar.
DTM     Bekräftat leveransdatum.
FTX Uppgifter för felanalys
RFF- DTM    Referensnummer
NAD     Köparens identitet (EAN lokaliseringsnummer).
        Leverantörens identitet (EAN lokaliseringsnummer).

LIN     Radnummer.
            EAN artikelnummer.
PIA     Kompletterande artikelnummer.
QTY Kvantitet.

UNS     Avslutar orderrad.
UNT     Avslutar ordermeddelandet.
"""

    _edi_lines_tot_qty = 0

    def _get_line_nr(self, order, inv_line):
        for line in order.order_line:
            if inv_line in line.invoice_lines:
                return line.sequence
        raise ValueError("Invoice line (id: %s) not found in order %s." % (inv_line.id, order.name))
    
    def _get_inv_line_nr(self, invoice, inv_line):
        nr = 1
        for line in invoice.invoice_line:
            if line.product_id == inv_line.product_id:
                return nr
            nr += 1
        raise ValueError("Invoice line (id: %s) not found in invoice %s." % (inv_line.id, order.name))
    
    @api.one
    def _pack(self):
        super(edi_message, self)._pack()
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_invoic').id:
            if self.model_record._name != 'account.invoice':
                raise ValueError("INVOIC: Attached record is not an account.invoice! {model}".format(model=self.model_record._name),self.model_record._name)
            invoice = self.model_record
            msg = self.UNH('INVOIC', ass_code='EAN008')
            #380 =  Commercial invoice - Document/message claiming payment for goods or services supplied under conditions agreed between seller and buyer.
            #381 =  Credit note - Document/message for providing credit information to the relevant party.
            #9 = Original - Initial transmission related to a given transaction.
            msg += self.BGM(381 if invoice.type == 'out_refund' else 380, invoice.number, 9)

            #Dates
            #Document date
            msg += self.DTM(137)
            #Actual delivery date
            act_date = None
            for picking in invoice.picking_ids:  # same as despatch-date
                if picking.date_done > act_date:
                    act_date = picking.date_done
            if act_date:
                msg += self.DTM(35, act_date)
            #Despatch date
            des_date = None
            for picking in invoice.picking_ids:
                if picking.date_done > des_date:
                    des_date = picking.date_done
            if des_date:
                msg += self.DTM(11, des_date)
            if invoice.type == 'out_refund':
                #Sanity checks
                if invoice.invoice_id and (invoice.credited_period_start or invoice.credited_period_end):
                    raise Warning("A credit invoice can not have both a Credited Invoice Reference and an Credited Invoice Period!")
                elif not (invoice.invoice_id or (invoice.credited_period_start and invoice.credited_period_end)):
                    raise Warning("A credit invoice must have either a Credited Invoice Reference or a Credited Invoice Period!")
                
                #Invoice Period
                if not invoice.invoice_id:
                    msg += self.DTM(167, invoice.credited_period_start)
                    msg += self.DTM(168, invoice.credited_period_end)
                
                #Invoice Reason
                if invoice.credit_reason:
                    msg += self.ALI(invoice.credit_reason)
                else:
                    raise Warning("A credit invoice must have a Credit Reason!")
                
                #Invoice Reference
                if invoice.invoice_id:
                    msg += self.RFF(invoice.invoice_id.name, 'IV')
                    
            order = invoice.order_ids and invoice.order_ids[0]
            #Contract reference
            if order and order.project_id and order.project_id.code:
                msg += self.RFF(order.project_id.code, 'CT')
            #Pricelist
            #msg += ...
            #Order reference
            if order:
                msg += self.RFF(order.client_order_ref or order.name, 'ON')
            for picking in invoice.picking_ids:
                msg += self.RFF(picking.name, 'DQ')
            #msg += self.RFF(foobar.desadv, 'AAK')


            msg += self.NAD_BY(picking.sale_id.partner_id)
            if self.consignee_id and self.consignee_id.vat:
                msg += self.RFF(self.consignee_id.vat, 'VA')

            if order and order.nad_dp:
                self.nad_dp = order.nad_dp.id
                msg += self.NAD_DP()

            if order and order.nad_ito:
                self.nad_ito = order.nad_ito.id
                msg += self.NAD_ITO()

            msg += self.NAD_SU()
            if self.consignor_id and self.consignor_id.vat:
                msg += self.RFF(self.consignor_id.vat, 'VA')

            #~ msg += self.NAD_CN()
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
                msg += self.PRI(line.price_unit)
                #Reference to invoice. Again?
                if order and invoice.type != 'out_refund':
                    msg += self.RFF(order.client_order_ref or order.name, 'ON', self._get_line_nr(order, line))
                if invoice.invoice_id and invoice.type == 'out_refund':
                    msg += self.RFF(invoice.invoice_id.name, 'IV', self._get_inv_line_nr(invoice.invoice_id, line))
                #Justification for tax exemption
                #TAX
            msg += self.UNS()
            msg += self.CNT(1, self._edi_lines_tot_qty)
            msg += self.CNT(2, self._lin_count)
            #Amount due
            msg += self.MOA(invoice.amount_total, 9)
            msg += self.MOA(0.0, 165)  # Adjustment amount. Amount being the balance of the amount to be adjusted and the adjusted amount.

            #Small change roundoff
            #self.msg += self.MOA()
            #Sum of all line items
            msg += self.MOA(invoice.amount_untaxed, 79)
            #Total taxable amount
            msg += self.MOA(invoice.amount_untaxed, 125)
            #Total taxes
            msg += self.MOA(invoice.amount_tax, 176)
            msg += self.MOA(0.0, 131)  # The amount specified is the total of all charges/allowances.

            #Total allowance/charge amount
            #self.msg += self.MOA(, 131)
            #TAX-MOA-MOA
            #self.msg += self.TAX()
            #self.msg += self.MOA()
            #self.msg += self.MOA()
            #TAX-MOA-MOAs
            for tax_line in invoice.tax_line:
                tax = self._get_account_tax(tax_line.name)
                msg += self.TAX(tax.amount * 100, tax_type = tax.gs1_tax_type, category = tax.gs1_tax_category) #Tax category and rate
                msg += self.MOA(tax_line.base_amount, 125)   # Taxable amount
                msg += self.MOA(tax_line.tax_amount, 124)  # Tax amount . Tax imposed by government or other official authority related to the weight/volume charge or valuation charge.
            msg += self.UNT()
            self.body = base64.b64encode(self._gs1_encode_msg(msg))

