from odoo import models, fields, api
import io
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import logging
import base64

_logger = logging.getLogger(__name__)


class CustomAccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    monochrome_threshold = fields.Integer(
        default=129,
        help='Set the contrast for image processing (0 to 255).'
    )

    displayed_image = fields.Binary(
        compute="_compute_displayed_image"
    )

    ocrlang = fields.Selection(
        [('swe', 'Swedish'), ('eng', 'English')],
        string='OCR Language',
        default='swe',
        help='Select the language for OCR text extraction.'
    )

    def open_same_wizard(self):
        return {
            "type": 'ir.actions.act_window',
            "view_mode": "form",
            "res_model": 'account.invoice.import',
            "res_id": self.id,
            "target": "new",
        }

    def preset_min(self):
        self.write({'monochrome_threshold': 70})
        return self.open_same_wizard()

    def preset_mid(self):
        self.write({'monochrome_threshold': 129})
        return self.open_same_wizard()

    def preset_max(self):
        self.write({'monochrome_threshold': 180})
        return self.open_same_wizard()

    @api.onchange('monochrome_threshold', 'invoice_file')
    def _compute_displayed_image(self):
        for record in self:
            if record.invoice_file:
                try:
                    file_data = base64.b64decode(record.invoice_file)
                    record.displayed_image = self._get_displayed_image(
                        file_data=file_data, monochrome_threshold=record.monochrome_threshold)
                except Exception as e:
                    _logger.warning("Image processing failed. Error: %s", e)
                    record.displayed_image = False
            else:
                record.displayed_image = False

    @api.model
    def _get_displayed_image(self, file_data, monochrome_threshold):
        try:
            images = convert_from_bytes(file_data)
            monochrome_images = [self._convert_to_monochrome(
                image, monochrome_threshold) for image in images]
            return self._combine_images(monochrome_images)
        except Exception as e:
            _logger.warning("Image processing failed. Error: %s", e)
            return False

    @api.model
    def _convert_to_monochrome(self, image, threshold):
        return image.convert('L').point(lambda p: p > threshold and 255)

    @api.model
    def _combine_images(self, images):
        widths, heights = zip(*(i.size for i in images))
        total_width = sum(widths)
        max_height = max(heights)
        new_image = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for image in images:
            new_image.paste(image, (x_offset, 0))
            x_offset += image.width
        return self._image_to_base64(new_image)

    @api.model
    def _image_to_base64(self, image):
        img_byte_array = io.BytesIO()
        image.save(img_byte_array, format='PNG')
        return base64.b64encode(img_byte_array.getvalue())

    @api.model
    def _simple_pdf_text_extraction_pytesseract(self, fileobj, test_info):
        res = False
        lang = self.ocrlang if self else "eng"
        monochrome_threshold = self.monochrome_threshold if self else 129
        try:
            pages = []
            images = convert_from_bytes(fileobj)

            def convert_to_monochrome(image):
                return image.convert('L').point(lambda p: p > monochrome_threshold and 255)

            for image in images:
                monochrome_image = convert_to_monochrome(image)
                image_text = pytesseract.image_to_string(
                    monochrome_image, lang=lang)
                pages.append(image_text)
            res = {
                "all": "\n".join(pages),
                "first": pages and pages[0] or "",
                "all_no_space": ("\n".join(pages)).replace(" ", "")
            }
            _logger.info("Text extraction made with pytesseract enhanced options")
            test_info["text_extraction"] = "pytesseract"
        except Exception as e:
            _logger.warning(
                "Text extraction with pytesseract failed. Error: %s", e)
        return res
