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
"""Tests for the NUL sanitizing.

The PDF fixture is generated on the fly. It contains the escape ``\\000``
inside a text string, which ``pypdf`` turns into a real NUL character in the
extracted text — exactly what breaks PostgreSQL.
"""

import io
from base64 import b64encode

import pypdf

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon

NUL = "\x00"


def _build_pdf_with_nul(
    text=r"Partner name: \000Test partner",
    line_text=r"Child,Street 1,",
    pad=9000,
):
    """Build a minimal one-page PDF whose text string contains an escaped NUL.

    ``pad`` keeps the file above Python's 8 KiB buffer size. The core module
    writes the temporary PDF with ``NamedTemporaryFile("wb")`` and reads it
    back without flushing, so anything smaller than one buffer block is still
    empty on disk when pypdf opens it.
    """
    content = (
        b"BT /F1 12 Tf 72 720 Td (" + text.encode("utf-8") + b") Tj "
        b"0 -20 Td (" + line_text.encode("utf-8") + b") Tj ET"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    if pad:
        out.write(b"%" + b"p" * pad + b"\n")
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % index + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n" % (len(objects) + 1))
    out.write(b"0000000000 65535 f \n")
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref)
    )
    return out.getvalue()


@tagged("post_install", "-at_install")
class TestPdfImportSanitize(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env["wizard.base.import.pdf.upload"]
        cls.mixin = cls.env["wizard.base.import.pdf.mixin"]
        pdf = _build_pdf_with_nul()
        cls.attachment = cls.env["ir.attachment"].create(
            {
                "name": "nul.pdf",
                "datas": b64encode(pdf),
            }
        )
        cls.pdf = pdf
        template = cls.env["base.import.pdf.template"].create(
            {
                "name": "NUL partner template",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "child_field_id": cls.env.ref("base.field_res_partner__child_ids").id,
                "auto_detect_pattern": "Partner name:.*",
            }
        )
        cls.env["base.import.pdf.template.line"].create(
            {
                "template_id": template.id,
                "related_model": "header",
                "field_id": cls.env.ref("base.field_res_partner__name").id,
                "pattern": r"Partner name:[ ](.*)",
            }
        )
        # En child-rad krävs: _get_table_info() kraschar (IndexError) om mallen
        # saknar "lines"-rader, oavsett om PDF:en har tabelldata eller ej.
        cls.env["base.import.pdf.template.line"].create(
            {
                "template_id": template.id,
                "related_model": "lines",
                "field_id": cls.env.ref("base.field_res_partner__name").id,
                "pattern": r"(.*),.*,",
            }
        )
        cls.template = template

    def test_pypdf_really_produces_a_nul(self):
        """Sanity check for the fixture: pypdf hands us a NUL character."""
        text = pypdf.PdfReader(io.BytesIO(self.pdf)).pages[0].extract_text()
        self.assertIn(NUL, text)

    def test_fallback_parse_pdf_strips_nul(self):
        wizard = self.env["wizard.base.import.pdf.preview"].create(
            {"extraction_mode": "pypdf"}
        )
        result = "".join(wizard._fallback_parse_pdf(self.pdf))
        self.assertNotIn(NUL, result)
        self.assertIn("Test partner", result)

    def test_parse_pdf_strips_nul(self):
        wizard = self.env["wizard.base.import.pdf.preview"].create(
            {"extraction_mode": "pypdf"}
        )
        result = "".join(wizard._parse_pdf(b64encode(self.pdf)))
        self.assertNotIn(NUL, result)

    def test_parse_pdf_grouped_strips_nul(self):
        line = self.env["wizard.base.import.pdf.upload.line"].create(
            {"attachment_id": self.attachment.id}
        )
        for pages in line._parse_pdf_grouped().values():
            if pages:
                self.assertNotIn(NUL, "".join(pages))

    def test_small_pdf_is_extracted(self):
        """A file below the write buffer must still reach the extractor.

        ``simple_pdf_text_extraction()`` writes the upload to a
        ``NamedTemporaryFile`` and then hands the *path* to pypdf, without
        flushing in between. Small files stayed in the buffer and read back as
        "Cannot read an empty file".
        """
        small = _build_pdf_with_nul(pad=0)
        self.assertLess(len(small), 8192)
        wizard = self.env["wizard.base.import.pdf.preview"].create(
            {"extraction_mode": "pypdf"}
        )
        result = wizard._fallback_parse_pdf(small)
        self.assertIn("Test partner", "".join(result))

    def test_sanitize_pdf_text_passthrough(self):
        self.assertEqual(self.mixin._sanitize_pdf_text("clean"), "clean")
        self.assertEqual(self.mixin._sanitize_pdf_text(b"bytes"), b"bytes")
        self.assertIsNone(self.mixin._sanitize_pdf_text(None))
        self.assertEqual(self.mixin._sanitize_pdf_text("a\x00b"), "ab")

    def test_upload_wizard_creates_the_record(self):
        """End to end: a PDF containing NUL imports without raising.

        Before this module the ``Form()`` onchange flushed ``"\\x00Test
        partner"`` to PostgreSQL and the wizard died with
        ``ValueError: A string literal cannot contain NUL (0x00) characters.``
        """
        wizard = self.wizard_model.create(
            {"model": "res.partner", "attachment_ids": self.attachment.ids}
        )
        res = wizard.action_process()
        record = self.env[res["res_model"]].browse(res["res_id"])
        self.assertEqual(record.name, "Test partner")
        self.assertNotIn(NUL, record.name)
