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
    'name': 'EDI AF AIS BOS',
    'version': '12.0.2.0.1',
    'category': 'edi',
    'summary': """
        Check if a postcode is valid for KROM.\n
        Returns an enum for postnummer from IPF AIS BOS Regelverk V2 API.
        """,
    'licence': 'AGPL-3',
    'description': """
Module for BOS KROM
================================================================================================
v12.0.2.0.0 AFC-1950 - Implemented new version of API \n
v12.0.2.0.1 AFC-1950 - Replaced match_area and updated index file \n
     """,
    'author': 'Arbetsförmedlingen',
    'website': 'https://arbetsformedlingen.se/',
    'depends': ['partner_view_360', 'edi_route_ipf'],
    'external_dependencies': {
    },
    'data': [
        'data/edi_route_data.xml',
        'views/edi_af_ais_bos_views.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
