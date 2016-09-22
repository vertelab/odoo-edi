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
    'name': 'EDI GS1 (Bergendahls)',
    'version': '0.1',
    'category': 'edi',
    'summary': 'GS1 Bergendahls additions ',
    'licence': 'AGPL-3',
    'description': """
Dummy module only used to import data from a specific client's customer registry.
Wizard for loading Bergendahls shops and adresses.
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['edi_gs1', 'partner_store_number'],
    'data': [
        'res_partner_view.xml',
        'bergendahls_data.xml',
    ],
    'external_dependencies': {'python': ['unicodecsv','openpyxl','urllib2']},
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
