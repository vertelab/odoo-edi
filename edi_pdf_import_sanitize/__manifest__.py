# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>)
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
# https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html
#
{
    'name': 'EDI: PDF Import Sanitize',
    'version': '18.0.1.0.0',
    'summary': """
        Strip NUL (0x00) characters from PDF text extraction so that
        base_import_pdf_by_template can import documents that contain them.""",
    'category': 'Extra Tools',
    'description': """
EDI: PDF Import Sanitize
========================

PDF text strings may legally contain NUL characters (``0x00``), e.g. as
``\\000`` escapes or as a positioning trick used by some PDF generators.
``pypdf`` returns them verbatim, and PostgreSQL rejects any string literal
containing ``0x00``::

    ValueError: A string literal cannot contain NUL (0x00) characters.

``base_import_pdf_by_template`` passes the extracted text straight into
``setattr()`` on a ``Form()``, which flushes the value to the database on
the next onchange. The import therefore fails with a raw traceback, and the
error handler ``_create_ir_logging()`` fails again on the same value because
it calls ``self.env.flush_all()`` before opening its own cursor.

This module fixes three things:

* ``_fallback_parse_pdf()`` is overridden so that NUL characters are removed
  from every extracted page *before* the text reaches the template parsing.
  The preview wizard, the auto-detection and the upload wizard all go through
  this single method.
* ``_create_ir_logging()`` is overridden so that the pending flush is done
  inside the ``try`` block. An error can then always be logged instead of
  masking the original exception with a second one.
* ``simple_pdf_text_extraction()`` is overridden to flush the temporary PDF
  before the extractor opens it by name. The original never flushes, so a
  small upload can read back as an empty file ("Cannot read an empty file"),
  which makes text extraction fail for reasons unrelated to the content.

The module is a drop-in: no views, no data, no configuration. It only
applies when ``base_import_pdf_by_template`` is installed.
""",
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-',
    'images': ['static/description/banner.png'],  # 560x280 px.
    'license': 'AGPL-3',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-edi.git',
    'depends': ['base_import_pdf_by_template'],
    'data': [],
    'application': False,
    'installable': True,
    'auto_install': False,
}
