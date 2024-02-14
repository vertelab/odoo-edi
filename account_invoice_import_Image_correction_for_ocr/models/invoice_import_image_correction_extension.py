from odoo import models, fields, api
from pdf2image import convert_from_bytes
import pytesseract
import regex
from PIL import Image
import logging

_logger = logging.getLogger(__name__)


class CustomAccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    monochrome_threshold = fields.Integer(
        string='Monochrome Threshold',
        default=129,
        help='Set the contrast for image processing (0 to 255).'
    )

    displayed_image = fields.Binary(
        string="Displayed Image",
        compute="_compute_displayed_image"
    )

    image_slider = fields.Integer(
        string="Image Slider",
        default=129,
        help="Slider to set the contrast for image processing (0 to 255)."
    )

    @api.onchange('image_slider', 'invoice_file')
    def _compute_displayed_image(self):
        _logger.warning("_compute_displayed_image"*100)
        for record in self:
            _logger.warning(
                f"Computing displayed_image for record ID {record.id}")
            if record.invoice_file:
                _logger.warning(f"File data present for record ID {record.id}")
                record.displayed_image = self._get_displayed_image(
                    convert_to_monochrome(record.invoice_file), monochrome_threshold=record.image_slider)

            else:
                _logger.warning(f"No file data for record ID {record.id}")
                record.displayed_image = False

    def _get_displayed_image(self, file_data, monochrome_threshold):
        try:
            _logger.warning("Attempting image processing for file data")
            images = convert_from_bytes(file_data)
            _logger.warning(f"Number of images: {len(images)}")

            def convert_to_monochrome(image):
                return image.convert('L').point(lambda p: p > monochrome_threshold and 255)

            monochrome_images = [
                convert_to_monochrome(image) for image in images]
            _logger.warning("Monochrome images processed successfully")
            return self._combine_images(monochrome_images)
        except Exception as e:
            _logger.warning("Image processing failed. Error: %s", e)
            return False

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

    def _image_to_base64(self, image):
        img_byte_array = io.BytesIO()
        image.save(img_byte_array, format='PNG')
        return base64.b64encode(img_byte_array.getvalue())
