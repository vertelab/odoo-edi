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
"""Make the error handler survive the error it is meant to log.

``_create_ir_logging()`` in ``base_import_pdf_by_template`` calls
``self.env.flush_all()`` *before* it opens its own cursor. When the original
exception was raised by that very flush (a value PostgreSQL refuses, e.g. a
string containing NUL), the flush raises again inside the error handler. The
user then sees a second traceback instead of the first one, and nothing is
logged at all.

We flush inside the ``try`` block, and discard the pending values if the
flush fails, so the log line is always written.
"""

import logging

import psycopg2

from odoo import api, models

_logger = logging.getLogger(__name__)


class WizardBaseImportPdfUpload(models.TransientModel):
    _inherit = "wizard.base.import.pdf.upload"

    @api.model
    def _create_ir_logging(self, message, func):
        try:
            self.env.flush_all()
        except Exception:  # noqa: BLE001 - the handler must never raise
            # The pending values are unusable (they are what broke the
            # original call). Drop them so that the fresh cursor below can
            # still write the log line.
            _logger.warning(
                "Could not flush before logging an error in %s; discarding "
                "the pending values",
                func,
                exc_info=True,
            )
            self.env.clear()
        return super()._create_ir_logging(message, func)
