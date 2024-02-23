# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from pdf2image import convert_from_bytes
import pytesseract
import logging
from odoo import models, fields, api, _
import subprocess
import pdfplumber
import base64
import tempfile
import binascii
from PIL import Image
import PyPDF2
import fitz
from PIL import Image
from odoo.exceptions import UserError
from PyPDF2 import PdfFileReader
import logging
from pdf2image import convert_from_path, convert_from_bytes
import shutil
import subprocess
from tempfile import NamedTemporaryFile

import logging

_logger = logging.getLogger(__name__)

try:
    import pytesseract
except ImportError:
    _logger.debug("Cannot import pytesseract")
try:
    import regex
except ImportError:
    _logger.debug("Cannot import regex")


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def simple_pdf_text_extraction(self, file_data, test_info):
        fileobj = NamedTemporaryFile(
            "wb", prefix="odoo-simple-pdf-", suffix=".pdf")
        fileobj.write(file_data)
        # Extract text from PDF
        # Very interesting reading:
        # https://dida.do/blog/how-to-extract-text-from-pdf
        # https://github.com/erfelipe/PDFtextExtraction
        specific_tool = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("invoice_import_simple_pdf.pdf2txt")
        )
        if specific_tool:
            specific_tool = specific_tool.strip().lower()
        test_info["text_extraction_config"] = specific_tool
        if specific_tool:
            res = self._simple_pdf_text_extraction_specific_tool(
                specific_tool, fileobj, test_info
            )

            if not res.get('all'):
                res = self._simple_pdf_text_extraction_pytesseract(
                    file_data, test_info)

        else:

            res = self._simple_pdf_text_extraction_pytesseract(
                file_data, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pymupdf(
                    fileobj, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pdftotext_lib(
                    fileobj, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pdftotext_cmd(
                    fileobj, test_info)
            if not res:
                res = self._simple_pdf_text_extraction_pdfplumber(
                    fileobj, test_info)
            if not res:
                raise UserError(
                    _(
                        "Odoo could not extract the text from the PDF invoice. "
                        "Refer to the Odoo server logs for more technical information "
                        "about the cause of the failure."
                    )
                )
        for key, text in res.items():
            if text:
                res[key] = regex.sub(test_info["lonely_accents"], "", text)

        res["all_no_space"] = regex.sub(
            "%s+" % test_info["space_pattern"], "", res["all"]
        )
        res["first_no_space"] = regex.sub(
            "%s+" % test_info["space_pattern"], "", res["first"]
        )
        fileobj.close()
        return res

    @api.model
    def _simple_pdf_text_extraction_pytesseract(self, fileobj, test_info):
        res = False
        try:
            pages = []

            images = convert_from_bytes(fileobj)
            for image in images:
                image_text = pytesseract.image_to_string(image)
                pages.append(image_text)

            res = {
                "all": "\n\n".join(pages),
                "first": pages and pages[0] or "",
            }
            _logger.info("Text extraction made with basic pytesseract ")
            test_info["text_extraction"] = "pytesseract"
        except Exception as e:
            _logger.warning(
                "Text extraction with pytesseract failed. Error: %s", e)
        return res
