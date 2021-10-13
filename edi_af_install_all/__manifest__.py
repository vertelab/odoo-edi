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
    'name': 'EDI AF Install modules',
    'version': '12.0.0.0.2',
    'category': 'edi',
    'summary': 'EDI AF  ',
    'licence': 'AGPL-3',
    'description': """ """,
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': [
        'af_data_ais-f_loader',
        'edi_af_aisf_trask',
        'edi_af_appointment',
        'edi_af_as_notes',
        'edi_af_officer',
        'edi_af_facility',
        'edi_af_aisf_ash_kom',
        ],
    'external_dependencies': {
    },
    'data': [
        
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
