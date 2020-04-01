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

class edi_envelope(models.Model):
    _inherit = 'edi.envelope' 
    
    @api.one
    def fold(self,route): # Folds messages in an envelope
        for m in self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',route.id)]):
            m.envelope_id = self.id
        envelope = super(edi_envelope,self).fold(route)
        if route.envelope_type == 'edifact':
            interchange_controle_ref = ''
            date = ''
            time = ''
            UNA = "UNA:+.? '"
            UNB = "UNB+UNOC:3+%s:14+%s:14+%s:%s+%s++ICARSP4'" % (route.partner_id.company_id.partner_id.gs1_gln, route.partner_id.gs1_gln, date, time, interchange_control_ref)
            body = ''.join([base64.b64decode(m.body) for m in envelope.message_ids])
            UNZ = "UNZ+%s+627'" % (len(envelope.message_ids),len(body))
            envelope.body = base64.b64encode(UNA + UNB + body + UNZ)
        return envelope

    def _create_UNB_segment(self,sender, recipient):
        self._seg_count += 1
        return "UNB+UNOC:3+%s:14+%s:14+%s:%s+%s++ICARSP4'" % (sender.gs1_gln, recipient.gs1_gln, date, time, interchange_control_ref)


class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    route_type = fields.Selection(selection_add=[('bis4a','Peppol BIS4A')])

class edi_message(models.Model):
    _inherit='edi.message'
    
    
    @api.model
    def _peppol_get_partner(self, tagd=None):
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
            raise Warning("Found more than one matching partner! scheme: %s. value: %s. partners: %s" % (scheme, text, [p.name for p in partner]))
        elif len(partner) == 1:
            return partner[0]
        return None
    
    @api.model
    def _peppol_find_partner(self, partnerd=None):
        if not partnerd:
            return None
        return _peppol_get_partner(
                partnerd.get('cbc:EndpointID')
            ) or _peppol_get_partner(
                partnerd.get(
                    'cac:PartyIdentification') and partnerd.get(
                        'cac:PartyIdentification').get('cbc:ID')
            ) or _peppol_get_partner(
                partnerd.get(
                    'cac:PartyTaxScheme') and partnerd.get(
                        'cac:PartyTaxScheme').get('cbc:CompanyID')
            ) or _peppol_get_partner(
                partnerd.get(
                    'cac:PartyLegalEntity' and partnerd.get(
                        'cac:PartyLegalEntity').get('cbc:CompanyID')
                )
            )
    

       

