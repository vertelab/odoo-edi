# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2022- Vertel AB (<https://vertel.se>).
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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'EDI: Import/Export Simple PDF Config',
    'version': '14.0.0.0.0',
    'summary': 'Import/Export Simple PDF Config',
    'category': 'EDI',
    'description': """
        Implements an Import/Export flow for Simple PDF Configurations
    """,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-edi/import_export_simple_pdf_config',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-edi',
    'depends': ['account_invoice_import_simple_pdf', 'contacts'],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/import_simple_pdf_config_view.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
