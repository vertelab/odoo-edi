
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
    'name': 'EDI PEPPOL',
    'summary': 'Module for sending and reciving PEPPOL',
    'author': 'Vertel AB',
    'contributor': '',
    'maintainer': 'Vertel AB',
    #'repository': 'https://github.com/vertelab/edi-peppol',
    'category': 'Accounting',
    'version': '14.0.0.0.0',
    # Version ledger: 14.0 = Odoo version. 1 = Major. Non regressionable code. 2 = Minor. New features that are regressionable. 3 = Bug fixes
    #'license': 'AGPL-3',
    'website': 'https://vertel.se/apps/odoo-edi/edi_peppol/',
    'description': """
        Implements a Framework for PEPPOL communication in Odoo.
        14.0.0.0.0 - Initial version
    """,
    'depends': ['base', 'l10n_se', 'edi_peppol_to_invoice', 'edi_peppol_to_order'],
    # Saxon-C-HE?
    #'external_dependencies': {
    #    'python': ['xlrd'],
    #},
    'data': [#'data/stylesheet-ubl.xslt',
             #'data/CEN-EN16931-UBL.sch',
             #'data/PEPPOL-EN16931-UBL.sch',
             #'data/iso_schematron_skeleton_for_saxon.xsl',
             #'data/instruction.toPeppol.csv',
             'views/account_invoice_view.xml',
             ],
    'installable': 'True',
    'application': 'False',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
