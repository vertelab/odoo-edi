# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Enterprise Management Solution, third party addon
#    Copyright (C) 2014-2021 Vertel AB (<http://vertel.se>).
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
    "name": "EDI Kontorsdatabasen",
    "description": """
Adds support for the REST API Kontorsdatabasen for the EDI framework in Odoo.
14.0.0.0.0 - Initial version
    """,
    "category": "EDI",
    "version": "14.0.0.0.0",
    "depends": [
        "edi_protocol_rest",
        "hr",
    ],
    "data": [
        "data/edi_rest_api_data.xml",
        "data/edi_route_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "author": "Vertel AB",
    "website": "www.vertel.se",
}