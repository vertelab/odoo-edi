# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _create_invoice_from_attachment(self, attachment_ids=None):
        """
        Create invoices from the attachments (for instance a Factur-X XML file)
        """
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            raise UserError(_("No attachment was provided"))

        invoices = self.env['account.move']
        for attachment in attachments:
            decoders = self.env['account.move']._get_create_invoice_from_attachment_decoders()
            invoice = False
            for decoder in sorted(decoders, key=lambda d: d[0]):
                invoice = decoder[1](attachment)
                if invoice:
                    break
            if not invoice:
                invoice = self.env['account.move'].create({})
            invoice.with_context(no_new_invoice=True).message_post(attachment_ids=[attachment.id])
            attachment.write({'res_model': 'account.move', 'res_id': invoice.id})
            self._try_with_account_invoice_import(invoice)
            invoices += invoice
        return invoices

    def _try_with_account_invoice_import(self, invoice):
        print("_try_with_account_invoice_import")
        # print(invoice.message_main_attachment_id.datas)
        invoice_import_id = self.env['account.invoice.import'].create({
            'invoice_file': invoice.message_main_attachment_id.datas,
            'invoice_filename': invoice.message_main_attachment_id.name
        })
        print(invoice_import_id)
        if invoice_import_id:
            invoice_import_id.import_invoice()
            # invoice_import_id.create_invoice_action_button()
