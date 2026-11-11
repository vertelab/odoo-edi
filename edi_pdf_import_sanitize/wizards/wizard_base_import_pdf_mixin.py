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
"""Remove NUL (0x00) characters from PDF text extraction.

PDF text strings may legally contain NUL characters, both as ``\\000``
escapes and as a positioning trick used by some PDF generators. ``pypdf``
returns them verbatim. PostgreSQL rejects any string literal containing
``0x00``, so the value blows up as soon as the ORM flushes it:

    ValueError: A string literal cannot contain NUL (0x00) characters.

``base_import_pdf_by_template`` feeds the extracted text straight into
``setattr()`` on a ``Form()``, which flushes on the next onchange. The import
therefore fails with a raw traceback instead of a readable message.

The single choke point is ``_fallback_parse_pdf()``: the preview wizard, the
auto-detection (``_parse_pdf_grouped``) and the upload wizard all call it. We
sanitize there, so the rest of the module never sees a NUL character.
"""

import logging

from odoo import models

_logger = logging.getLogger(__name__)

NUL = "\x00"


class WizardBaseImportPdfMixin(models.AbstractModel):
    _inherit = "wizard.base.import.pdf.mixin"

    def _sanitize_pdf_text(self, value):
        """Remove NUL characters from a single extracted text value.

        Only ``str`` is touched; the extraction methods return a list of
        page strings, but a custom ``extraction_mode`` may return something
        else, which is then passed through untouched.
        """
        if isinstance(value, str) and NUL in value:
            return value.replace(NUL, "")
        return value

    def _fallback_parse_pdf(self, file_data):
        res = super()._fallback_parse_pdf(file_data)
        if not res:
            return res
        if isinstance(res, str):
            return self._sanitize_pdf_text(res)
        if isinstance(res, (list, tuple)):
            sanitized = [self._sanitize_pdf_text(item) for item in res]
            if sanitized != list(res):
                _logger.info(
                    "Removed NUL (0x00) characters from the extracted PDF text "
                    "of %s",
                    self.attachment_id.name or "the uploaded file",
                )
            return sanitized
        return res
