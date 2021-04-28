# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2021 Vertel AB (<http://vertel.se>).
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
    'name': 'EDI AF Facility',
    'version': '12.0.2.0.0',
    'category': 'edi',
    'summary': 'EDI AF facility - Find bookable offices for meetings ',
    'licence': 'AGPL-3',
    'description': 
    """
Asks the Service Now On Site Operations API for all operations \n
then creates or updates operations and locations. \n
================================================================================================ \n
This functionality is tailored for AF. \n
v12.0.1.0.0: versions before good version control \n
v12.0.2.0.0 AFC-1766: Major overhaul of how the module works. \n
\n
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['partner_view_360', 'edi_route_ipf'],
    'external_dependencies': {
    },
    'data': [
        'data/edi_route_data.xml',
        'views/edi_af_facility_views.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
