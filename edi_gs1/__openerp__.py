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

{
    'name': 'EDI GS1',
    'version': '0.1',
    'category': 'edi',
    'summary': 'GS1 – the global language of business',
    'licence': 'AGPL-3',
    'description': """
Global Trade Item Number (GTIN)
http://www.gs1.se/en/Standards/Identify/gtin/

Serial Shipping Container Code (SSCC)
http://www.gs1.se/en/Standards/Identify/sscc/

Global Location number (GLN)
http://www.gs1.se/en/Standards/Identify/gln/

GS1 Company prefix

Consignor - the party sending the goods.
Consignee - the party receiving the goods.
Forwarder - the party planning the transport on behalf of the consignor or consignee.
Carrier - the party transporting the goods between two points.

Order
Order Response
Invoice
Despatch_advice

""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['edi_route','mail','product'],
    'data': [ 'res_partner_view.xml','product_view.xml','res_company_view.xml',
    #'security/ir.model.access.csv',
    ],
    'application': False,
    'installable': True,
 #   'demo': ['calendar_ics_demo.xml',],
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
