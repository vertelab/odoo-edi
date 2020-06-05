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
    'name': 'EDI Routes Mail',
    'version': '0.3',
    'category': 'edi',
    'summary': 'Routes for EDI using Mail',
    'licence': 'AGPL-3',
    'description': """
Add routes for EDI using Odoo Mail

""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['edi_route','mail'],
    'data': [ 'edi_route_view.xml',"edi_route_mail_data.xml",
    #'security/ir.model.access.csv',
    ],
    'application': False,
    'installable': True,
 #   'demo': ['calendar_ics_demo.xml',],
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
