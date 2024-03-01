from odoo import api, fields, models, _
from odoo import models, fields, api
import io
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import logging
import base64
from odoo.exceptions import UserError
from odoo.tools.misc import format_amount, format_date, format_datetime


_logger = logging.getLogger(__name__)
ERROR_STYLE = ' style="color:red;"'


class ResPartner(models.Model):
    _inherit = "res.partner"

    monochrome_threshold = fields.Integer(
        string='Monochrome Threshold',
        default=129,
        help='Set the contrast for image processing (0 to 255).'
    )

    displayed_image = fields.Binary(
        string="Displayed Image",
        compute="_compute_displayed_image"
    )

    ocrlang = fields.Selection(
        [('swe', 'Swedish'), ('eng', 'English')],
        string='OCR Language',
        default='swe',
        help='Select the language for OCR text extraction.'
    )

    def open_same_wizard(self):
        action = self.env.ref(
            'account_invoice_import_Image_correction_for_ocr.invoice_import_image_correction_action', raise_if_not_found=False)
        if action:
            return {
                "type": 'ir.actions.act_window',
                "view_mode": "form",
                "res_model": 'account.invoice.import',
                "res_id": action.id,
                "target": "new",
            }
        else:
            _logger.warning(
                "Action not found. Please check if the external ID is correct.")
            return {'type': 'ir.actions.act_window_close'}

    def _simple_pdf_text_extraction_pytesseract(self, fileobj, test_info, monochrome_threshold=129):
        self.ensure_one()
        aiio = self.env["account.invoice.import"]
        return aiio._simple_pdf_text_extraction_pytesseract(fileobj, test_info, monochrome_threshold)

    def preset_min(self):
        self.write({'monochrome_threshold': 70})
        return self.open_same_wizard()

    def preset_mid(self):
        self.write({'monochrome_threshold': 129})
        return self.open_same_wizard()

    def preset_max(self):
        self.write({'monochrome_threshold': 180})
        return self.open_same_wizard()

    @api.onchange('monochrome_threshold', 'simple_pdf_test_file')
    def _compute_displayed_image(self):
        aiio = self.env["account.invoice.import"]
        if self.simple_pdf_test_file:
            try:
                file_data = base64.b64decode(self.simple_pdf_test_file)
                self.displayed_image = aiio._get_displayed_image(
                    file_data=file_data, monochrome_threshold=self.monochrome_threshold)

            except Exception as e:
                _logger.warning("Image processing failed. Error: %s", e)
                self.displayed_image = False
        else:
            self.displayed_image = False

    def run_test_on_pdf_modification(self):
        _logger.warning("RUN TWICE ASWELL?"*100)
        self.ensure_one()

        aiio = self.env["account.invoice.import"].create(
            {'monochrome_threshold': self.monochrome_threshold,
             "ocrlang": self.ocrlang})

        rpo = self.env["res.partner"]
        vals = {}
        test_results = []
        test_results.append("<small>%s</small><br/>" % _("Errors are in red."))
        test_results.append(
            "<small>%s %s</small><br/>"
            % (_("Test Date:"), format_datetime(self.env, fields.Datetime.now()))
        )
        if not self.simple_pdf_test_file:
            raise UserError(_("You must upload a test PDF invoice."))

        test_info = {"test_mode": True}
        aiio._simple_pdf_update_test_info(test_info)
        file_data = base64.b64decode(self.simple_pdf_test_file)

        _logger.warning(f"\n\n\n{test_info=}\n\n\n")

        # raw_text_dict = aiio._simple_pdf_text_extraction_pytesseract(
        #    file_data, test_info, monochrome_threshold=self.monochrome_threshold, lang=self.ocrlang)

        raw_text_dict = aiio.simple_pdf_text_extraction(file_data, test_info)

        _logger.warning(f"after \n\n\n\n{test_info=}\n\n\n")

        test_results.append(
            "<small>%s %s</small><br/>"
            % (
                _("Text extraction system parameter:"),
                test_info.get("text_extraction_config") or _("none"),
            )
        )
        test_results.append(
            "<small>%s %s</small><br/>"
            % (_("Text extraction tool used:"), test_info.get("text_extraction"))
        )
        if self.simple_pdf_pages == "first":
            vals["simple_pdf_test_raw_text"] = raw_text_dict["first"]
        else:
            vals["simple_pdf_test_raw_text"] = raw_text_dict["all"]
        test_results.append("<h3>%s</h3><ul>" % _("Searching Partner"))
        partner_id = aiio.simple_pdf_match_partner(
            raw_text_dict.get("all_no_space", ""), test_results
        )
        partner_ok = False
        if partner_id:
            partner = rpo.browse(partner_id)
            if partner_id == self.id:
                partner_ok = True
                partner_result = _("Current partner found")
            else:
                partner_result = "%s %s" % (
                    _("Found another partner:"),
                    partner.display_name,
                )
        else:
            partner_result = _("No partner found.")

        test_results.append(
            "<li><b>%s</b> <b%s>%s</b></li></ul>"
            % (_("Result:"), not partner_ok and ERROR_STYLE or "", partner_result)
        )
        if partner_ok:
            partner_config = self._simple_pdf_partner_config()
            test_results.append("<h3>%s</h3><ul>" % _("Amount Setup"))
            test_results.append(
                """<li>%s "%s" (%s)</li>"""
                % (
                    _("Decimal Separator:"),
                    partner_config["decimal_sep"],
                    partner_config["char2separator"].get(
                        partner_config["decimal_sep"], _("unknown")
                    ),
                )
            )
            test_results.append(
                """<li>%s "%s" (%s)</li></ul>"""
                % (
                    _("Thousand Separator:"),
                    partner_config["thousand_sep"],
                    partner_config["char2separator"].get(
                        partner_config["thousand_sep"], _("unknown")
                    ),
                )
            )
            parsed_inv = aiio.simple_pdf_parse_invoice(file_data, test_info)
            key2label = {
                "pattern": _("Regular Expression"),
                "date_format": _("Date Format"),
                "res_regex": _("Raw List"),
                "valid_list": _("Valid-data Filtered List"),
                "sorted_list": _("Ordered List"),
                "error_msg": _("Error message"),
                "start": _("Start String"),
                "end": _("End String"),
            }
            for field in self.simple_pdf_field_ids:
                test_results.append(
                    "<h3>%s</h3><ul>" % test_info["field_name_sel"][field.name]
                )
                extract_method = test_info["extract_rule_sel"][field.extract_rule]
                if field.extract_rule.startswith("position_"):
                    extract_method += _(", Position: %d") % field.position
                test_results.append(
                    "<li>%s %s</li>" % (_("Extract Rule:"), extract_method)
                )
                for key, value in test_info[field.name].items():
                    if key != "pattern" or self.env.user.has_group("base.group_system"):
                        test_results.append("<li>%s: %s</li>" %
                                            (key2label[key], value))

                result = parsed_inv.get(field.name)
                if "date" in field.name and result:
                    result = format_date(self.env, result)
                if "amount" in field.name and result:
                    result = format_amount(
                        self.env, result, parsed_inv["currency"]["recordset"]
                    )
                test_results.append(
                    "<li><b>%s</b> <b%s>%s</b></li></ul>"
                    % (
                        _("Result:"),
                        not result and ERROR_STYLE or "",
                        result or _("None"),
                    )
                )
        _logger.warning(f"\n\n\n{vals=}\n\n\n")
        vals["simple_pdf_test_results"] = "\n".join(test_results)
        self.write(vals)
