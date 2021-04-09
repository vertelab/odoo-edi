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
    'name': 'EDI AF TRASK Arbetssökande',
    'version': '12.0.1.0.0',
    'category': 'edi',
    'summary': 'EDI AF TRASK arbetssökande - support for jobseekers ',
    'licence': 'AGPL-3',
    'description': """
EDI AF TRASK Arbetssökande
===============================================================================
This module handles integration with AF TRASK-system.\n
v12.0.0.0.1: Versions before good version control \n
v12.0.1.0.0 AFC-1920: Minor fixes with regards to the new structure\n
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': [
        'edi_route_ipf',
        'edi_af_appointment'
        ],
    'external_dependencies': {
    },
    'data': [
        'data/edi_route_data.xml',
        'views/edi_af_aisf_trask_views.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
