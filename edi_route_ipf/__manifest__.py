# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
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
    'name': 'EDI Routes IPF',
    'version': '12.0.2.1.0',
    'category': 'edi',
    'summary': 'Routes for EDI using IPF',
    'licence': 'AGPL-3',
    'description': """
Add routes for EDI using IPF-Rest and IPF-MQ.
================================================================================================
Requires python libraries paramiko and pycrypto. http://www.paramiko.org/installing.html
This functionality is tailored for AF. \n
v12.0.1.0.0: versions before good version control \n
v12.0.2.0.0 AFC-1766: Major overhaul of how the module works. \n
v12.0.2.1.0 AFC-1767: Implemented edi.log model. \n
\n
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['edi_route',],
    'data': [ 
        'views/edi_route_view.xml', 
        'views/edi_message_view.xml', 
        'views/edi_type_view.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
