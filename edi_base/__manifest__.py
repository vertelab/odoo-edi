# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) {year} {company} (<{mail}>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
#
# https://www.odoo.com/documentation/14.0/reference/module.html
#
{
    'name': 'EDI: Base',
    'version': '1.0',
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.odoo.com""",
    'category': '', # Technical Settings|Localization|Payroll Localization|Account Charts|User types|Invoicing|Sales|Human Resources|Operations|Marketing|Manufacturing|Website|Theme|Administration|Appraisals|Sign|Helpdesk|Administration|Extra Rights|Other Extra Rights|
    'description': """
        Long description of module's purpose
    """,
    #'sequence': 1,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-',
    'images': ['static/description/banner.png'], # 560x280
    'license': 'AGPL-3',
    'depends': ['account_edi_ubl_cii'],
     #"external_dependencies": {
     #   "bin": ["openssl",], 
     #   "python": ["acme_tiny", "IPy",],
     #},
    'data': [
        'security/ir.model.access.csv',
        'views/edi_envelope_view.xml',
        'views/edi_message_view.xml',
        'views/edi_transport_view.xml',
        'views/edi_route_view.xml',
        'views/edi_route_line_view.xml',
        'views/edi_session_view.xml',
        'views/edi_session_line_view.xml',
        'views/res_partner_inherited_view.xml',
        'views/edi_message_format_view.xml',
        'views/menu.xml',
        'wizard/edi_envelope_wizard.xml',
        'data/edi_message_format.xml',
    ],
    'demo': [],
    'application': False,
    'installable': True,    
    'auto_install': False,
    #"post_init_hook": "post_init_hook",
}
