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
    'name': 'EDI Peppol',
    'version': '0.1',
    'category': 'edi',
    'summary': 'PEPPOL – Pan-European Public Procurement Online',
    'licence': 'AGPL-3',
    'description': """

Implementation of PEPPOL BIS 5A 2.0 (Invoice)  Svefaktura BIS 5A 2.0

https://sfti.validex.net/en/login
https://portal.gefeg.com/validationportal/



PEPPOL Business Interoperability Specifications -BIS

 +-------------------+-------------+---------------+
 | EDI standard      | Implemented |  in / out     |
 +-------------------+-------------+---------------+
 | BIS 5a 2.0 Invoice|      Y      |  in           |
 +-------------------+-------------+---------------+
 | BIS 5a 2.0 Credit |      N      |               |
 +-------------------+-------------+---------------+


About OpenPEPPOL

The purpose of OpenPEPPOL is to enable European businesses to easily deal electronically with any European public sector buyers in their procurement processes, 
thereby increasing opportunities for greater competition for government contracts and providing better value for tax payers’ money.
Business to business use of the PEPPOL-compliant infrastructure and use of PEPPOL-components in other areas beyond procurement are 
also recognised as important and is encouraged by the Association. 

""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['edi_route','account'],
    'external_dependencies': {
        'python': ['xmltodict'],
    },
    'data': [
        'account_invoice_data.xml',
    ],
    'application': False,
    'installable': True,
 #   'demo': ['calendar_ics_demo.xml',],
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
