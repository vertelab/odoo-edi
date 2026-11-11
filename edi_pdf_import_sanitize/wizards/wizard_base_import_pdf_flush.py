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
"""Flush the temporary PDF before the extractor opens it by name.

``simple_pdf_text_extraction()`` in ``base_import_pdf_by_template`` writes
the uploaded file to a ``NamedTemporaryFile`` and then hands the *path* to the
extraction method, which opens the file a second time. The buffered writer is
never flushed, so the second reader may see an empty (or truncated) file:

    WARNING Text extraction with pypdf failed. Error: Cannot read an empty file
    UserError: Odoo could not extract the text from the PDF.

Whether it fails depends only on the file size and the buffer, i.e. on the
customer's PDF — not on anything the user did. Adding the missing flush makes
extraction independent of file size.
"""

import logging

from tempfile import NamedTemporaryFile

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardBaseImportPdfMixin(models.AbstractModel):
    _inherit = "wizard.base.import.pdf.mixin"

    def simple_pdf_text_extraction(self, file_data):
        fileobj = NamedTemporaryFile("wb", prefix="odoo-simple-pdf-", suffix=".pdf")
        try:
            fileobj.write(file_data)
            # The extractor below opens the file by name: the data has to reach
            # the filesystem first, otherwise a small file reads back as empty.
            fileobj.flush()
            method = f"_pdf_text_extraction_{self.extraction_mode}"
            res = False
            if hasattr(self, method):
                res = getattr(self, method)(fileobj)
        finally:
            fileobj.close()
        if not res:
            raise UserError(_("Odoo could not extract the text from the PDF."))
        return res
