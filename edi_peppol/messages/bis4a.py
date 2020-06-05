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
from lxml import etree
import xmltodict
import base64
from datetime import datetime
import re
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)

class edi_message(models.Model):
    _inherit='edi.message'
            
    def _peppol_build_invoice_diff_msg(self, total, untaxed, tax, lines, charges, allowances):
        msg = """
\nCalculated invoice does not match received invoice!
Total amount: %s
Untaxed amount: %s
Tax amount: %s

Lines
"""
        for line in lines:
            msg += line
        if charges:
            msg += "\nCharges\n"
            for charge in charges:
                msg += charge
        if allowances:
            msg += "\nAllowances\n"
            for allowance in allowances:
                msg += allowance
        return msg
    
    def _peppol_create_inv_line(self, line):
        res = (0, {
           'name': '',
           'quantity': 0.0,
           'price_unit': None,
        })
        
        res['product_id'] = None
    
    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_peppol.edi_message_type_bis4a').id:
            msgd = xmltodict.parse(base64.b64decode(self.body))
            invd = msgd.get('Invoice')
            if not invd:
                raise Warning('No Invoice in message!')
            node = invd.get('cac:AccountingSupplierParty') and invd.get('cac:AccountingSupplierParty').get('cac:Party')
            supplier = _peppol_find_partner(node)
            node = invd.get('cac:AccountingCustomerParty') and invd.get('cac:AccountingCustomerParty').get('cac:Party')
            buyer = _peppol_find_partner(node)
            node = invd.get('cac:PayeeParty')
            payee = _peppol_find_partner(node)
            ref = invd.get('cac:OrderReference') and invd.get('cac:OrderReference').get('cbc:ID')
            order = self.env['purchase.order'].search(['|', ('name', '=', ref), ('partner_ref', '=', ref)])
            if len(order) > 1:
                raise Warning('Found multiple matching purchase orders! reference: %s. orders: %s' % (ref, [o.name for o in order]))
            elif len(order) != 1:
                raise Warning("Couldn't find a purchase order matching reference '%s'!" % ref)
            else:
                order = order[0]
            payment_ref = invd.get('cac:PaymentMeans') and invd.get('cac:PaymentMeans').get('cbc:PaymentID')
            node = invd.get('cac:LegalMonetaryTotal')
            #Sum of line amounts
            lineExtensionAmount = node.get('cbc:LineExtensionAmount') and node.get('cbc:LineExtensionAmount').get('#text')
            lineExtensionCurrency = node.get('cbc:LineExtensionAmount') and node.get('cbc:LineExtensionAmount').get('@currencyID')
            #Invoice total amount without VAT
            taxExclusiveAmount = node.get('cbc:TaxExclusiveAmount') and node.get('cbc:TaxExclusiveAmount').get('#text')
            taxExclusiveCurrency = node.get('cbc:TaxExclusiveAmount') and node.get('cbc:TaxExclusiveAmount').get('@currencyID')
            #Invoice total amount with VAT
            taxInclusiveAmount = node.get('cbc:TaxInclusiveAmount') and node.get('cbc:TaxInclusiveAmount').get('#text')
            taxInclusiveCurrency = node.get('cbc:TaxInclusiveAmount') and node.get('cbc:TaxInclusiveAmount').get('@currencyID')
            #Allowance/discounts on document level
            allowanceTotalAmount = node.get('cbc:AllowanceTotalAmount') and node.get('cbc:AllowanceTotalAmount').get('#text')
            allowanceTotalCurrency = node.get('cbc:AllowanceTotalAmount') and node.get('cbc:AllowanceTotalAmount').get('@currencyID')
            #Charges on document level
            chargeTotalAmount = node.get('cbc:ChargeTotalAmount') and node.get('cbc:ChargeTotalAmount').get('#text')
            chargeTotalCurrency = node.get('cbc:ChargeTotalAmount') and node.get('cbc:ChargeTotalAmount').get('@currencyID')
            #The amount prepaid
            prepaidAmount = node.get('cbc:PrepaidAmount') and node.get('cbc:PrepaidAmount').get('#text')
            prepaidCurrency = node.get('cbc:PrepaidAmount') and node.get('cbc:PrepaidAmount').get('@currencyID')
            #The amount used to round
            payableRoundingAmount = node.get('cbc:PayableRoundingAmount') and node.get('cbc:PayableRoundingAmount').get('#text')
            payableRoundingCurrency = node.get('cbc:PayableRoundingAmount') and node.get('cbc:PayableRoundingAmount').get('@currencyID')
            #Final amount to be paid
            payableAmount = node.get('cbc:PayableAmount') and node.get('cbc:PayableAmount').get('#text')
            payableCurrency = node.get('cbc:PayableAmount') and node.get('cbc:PayableAmount').get('@currencyID')
            currency = None
            for c in [lineExtensionCurrency, taxExclusiveCurrency, taxExclusiveCurrency, taxInclusiveCurrency, allowanceTotalCurrency, chargeTotalCurrency, prepaidCurrency, payableRoundingCurrency, payableCurrency]:
                if not currency:
                    currency = c
                else:
                    if currency != c:
                        raise Warning("Multiple currencies in one invoice!")
            if not currency:
                raise Warning("No currency specified in invoice!")
            currency_obj = self.env['res.currency'].search([('name', '=', currency)])
            if len(currency_obj) > 1:
                raise Warning("Found multiple matching currencies! Currency code: %s" % currency)
            elif len(currency_obj) != 1:
                raise Warning("No matching currency found! Currency code: %s" % currency)
            currency_obj = currency_obj[0]
            lines = charges = allowances = []
            if order:
                invoice = order.view_invoice().get('res_id')
                if not invoice:
                    raise Warning("Couldn't create invoice!")
                invoice = self.env['account.invoice'].browse(invoice)
                invoice.reference = payment_ref or ref
                total = float(payableAmount)
                untaxed = float(taxExclusiveAmount)
                tax = float(taxInclusiveAmount) - float(taxExclusiveAmount)
                if invoice.amount_untaxed != untaxed or invoice.amount_tax != tax or invoice.amount_total != total:
                    invoice.comment += _peppol_build_invoice_diff_msg(total, untaxed, tax, lines, charges, allowances)
            else:
                invoice.create({
                    
                })
            
            
        else:
            super(edi_message, self).pack()
                
    
    @api.one
    def pack(self):
        super(edi_message, self).pack()
        if self.edi_type.id == self.env.ref('edi_peppol.edi_message_type_bis4a').id:
            if not self.model_record or self.model_record._name != 'account.invoice':
                raise Warning("INVOIC: Attached record is not an account.invoice! {model}".format(model=self.model_record and self.model_record._name or None))
            invoice = self.model_record
            
            root = etree.Element('Invoice',
                attrib={
                    'xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
                },
                nsmap={
                    'cac':  'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                    'cbc':  'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
                    'ccts': 'urn:un:unece:uncefact:documentation:2',
                    'qdt':  'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2',
                    'udt':  'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2',
                    
                }
            )

            raise Warning('Not implemented yet')
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

