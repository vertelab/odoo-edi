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
from lxml import etree
import xmltodict
import base64
from datetime import datetime
import re
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)

class edi_route(models.Model):
    _inherit = 'edi.route' 
    edi_type = fields.Selection(selection_add=[('invoice bis4a','Invoice BIS 4A')]) 

class edi_message(models.Model):
    _inherit='edi.message'
        
    edi_type = fields.Selection(selection_add = [('invoice bis4a','Invoice BIS 4A')])
    
    _edi_lines_tot_qty = 0
    
    @api.model
    def _bis4a_get_partner(self, tagd):
        """
GLN         GS1                                                                             0088
DUNS        Dun & Bradstreet                                                                0062
IBAN        S.W.I.F.T. Society for Worldwide Interbank Financial Telecommunications s.c.    0021
ISO6523     ISO (International Organization for Standardization)                            0028
DK:CPR      Danish Ministry of the Interior and Health                                      9901
DK:CVR      The Danish Commerce and Companies Agency                                        9902
DK:P        The Danish Commerce and Companies Agency                                        0096
DK:SE       Danish Ministry of Taxation, Central Customs and Tax Administration             9904
DK:VANS     Danish VANS providers                                                           9905
IT:VAT      Ufficio responsabile gestione partite IVA                                       9906
IT:CF       TAX Authority                                                                   9907
IT:FTI      Ediforum Italia                                                                 0097
IT:SIA      Società Interbancaria per l’Automazione             0135
IT:SECETI   Servizi Centralizzati SECETI            0142
NO:ORGNR    Enhetsregisteret ved Bronnoysundregisterne                  9908
NO:VAT      Enhetsregisteret ved Bronnoysundregisterne          9909    
HU:VAT                  9910
SE:ORGNR                0007
FI:OVT      Finnish tax board              0037
EU:VAT      National ministries of Economy                  9912
EU:REID     Business Registers Network              9913
FR:SIRET    INSEE: National Institute for statistics and Economic studies           0009
AT:VAT      Österreichische Umsatzsteuer-Identifikationsnummer               9914
AT:GOV      Österreichisches Verwaltungs bzw. Organisationskennzeichen                9915
AT:CID      Firmenidentifikationsnummer der Statistik Austria           9916
IS:KT       Icelandic National Registry                 9917
"""
        if not tagd:
            return None
        partner = []
        scheme = tagd.get('@schemeID')
        text = tagd.get('#text')
        if not text:
            return None
        elif scheme == 'GLN':
            partner = self.env['res.partner'].search([('gs1_gln', '=', text)])
        elif re.match(r'.*:VAT', scheme):
            partner = self.env['res.partner'].search([('vat', '=', text)])
        if len(partner) > 1:
            raise Warning("Found more than one matching partner! %s: %s" % (scheme, text))
        elif len(partner) == 1:
            return partner[0]
        return None
    
    @api.model
    def _bis4a_find_partner(self, partnerd):
        return _bis4a_get_partner(partnerd.get('cbc:EndpointID')) or _bis4a_get_partner(partnerd.get('cac:PartyIdentification') and partnerd.get('cac:PartyIdentification').get('cbc:ID'))
    
    @api.one
    def unpack(self):
        if self.edi_type == 'invoice bis4a':
            msgd = xmltodict.parse(base64.b64decode(self.body))
            invd = msgd.get('Invoice')
            if not invd:
                raise Warning('No Invoice in message!')
            node = invd.get('cac:AccountingSupplierParty') and invd.get('cac:AccountingSupplierParty').get('cac:Party')
            supplier = _bis4a_find_partner(node)
            node = invd.get('cac:AccountingCustomerParty') and invd.get('cac:AccountingCustomerParty').get('cac:Party')
            buyer = _bis4a_find_partner(node)
            
        else:
            super(edi_message, self).pack()
                
    
    @api.one
    def pack(self):
        super(edi_message, self).pack()
        if self.edi_type == 'invoice bis4a':
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

