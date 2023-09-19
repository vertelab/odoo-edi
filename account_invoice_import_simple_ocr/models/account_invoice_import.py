# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api, _
import subprocess
import pytesseract  ## $ sudo pip install pytesseract
import pdfplumber
from base64 import b64decode
import tempfile
from PIL import Image
import PyPDF2

import logging
import shutil
import subprocess
from tempfile import NamedTemporaryFile

import logging

_logger = logging.getLogger(__name__)

try:
    import pytesseract
except ImportError:
    _logger.debug("Cannot import pytesseract")


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def fallback_parse_pdf_invoice(self, file_data):
        """This method must be inherited by additional modules with
        the same kind of logic as the account_bank_statement_import_*
        modules"""
        res = super().fallback_parse_pdf_invoice(file_data)
        if not res:
            res = self.ocr_parse_invoice(file_data)
        return res

    def ocr_parse_invoice(self, file_data):
        all_text = ''
        with tempfile.NamedTemporaryFile('w+b', suffix='.pdf') as tmpfile:
            data_bytes = b64decode(file_data, validate=True)
            tmpfile.write(data_bytes)
            tmpfile.seek(0)
            with pdfplumber.open(tmpfile.name) as pdf:
                for page in pdf.pages:
                    page_content = page.extract_text(layout=True)
                    all_text = all_text + '\n' + page_content
        return all_text
