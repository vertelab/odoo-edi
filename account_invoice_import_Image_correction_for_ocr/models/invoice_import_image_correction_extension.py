from odoo import models, fields, api, _
from odoo.exceptions import UserError
import regex

class Account_Invoice_Import_Custom_Image_Correction(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def simple_pdf_text_extraction(self, file_data, test_info):


        result = super().simple_pdf_text_extraction(file_data, test_info)


        return result