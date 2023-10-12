# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import email
import email.policy
import logging
import xmlrpc.client as xmlrpclib

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_set_main_attachment_id(self, attachment_ids):  # todo move this out of mail.thread
        res = super()._message_set_main_attachment_id(attachment_ids)

        if self._name == 'account.move' and self._message_set_main_attachment_id:
            try:
                # Parse Using import wizard
                invoice_import_id = self.env['account.invoice.import'].create({
                    'invoice_file': self.message_main_attachment_id.datas,
                    'invoice_filename': self.message_main_attachment_id.name,
                    'invoice_id': self.id,
                })
                parsed_info = invoice_import_id.get_parsed_invoice()
                _logger.warning(f"{parsed_info['partner']['recordset']=}")
                existing_inv = invoice_import_id.invoice_already_exists(parsed_info["partner"]["recordset"],
                                                                        parsed_info)

                partner_id = parsed_info['partner']['recordset']
                company_id = self.env.context.get("force_company") or self.env.company.id

                aiico = self.env["account.invoice.import.config"]
                import_config_id = aiico.search(
                    [("partner_id", "=", partner_id.id), ("company_id", "=", company_id)], limit=1
                )

                import_config = import_config_id.convert_to_import_config()

                parsed_info = invoice_import_id._prepare_create_invoice_vals(parsed_info, import_config)

                if existing_inv:
                    message = _(
                        "This invoice already exists in Odoo. It's "
                        "Supplier Invoice Number is '%s' and it's Odoo number "
                        "is '%s'"
                    ) % (parsed_info.get("invoice_number"), existing_inv.name)
                    # self.message_post(body=message,message_type="comment",)

                    existing_invoice = self.env['account.move'].browse(existing_inv.id)
                    existing_invoice.to_check = True
                else:
                    partner_id = parsed_info.get('partner_id')

                    self.partner_id = partner_id
                    invoice_import_id.invoice_file = self.message_main_attachment_id.datas
                    invoice_import_id.invoice_filename = self.message_main_attachment_id.name
                    invoice_import_id.invoice_id = self
                    invoice_import_id.amount_untaxed = parsed_info.get('amount_untaxed', 0)
                    invoice_import_id.amount_total = parsed_info.get('amount_total', 0)
                    invoice_import_id.import_config_id = import_config_id
                    if not self.partner_id:
                        self.partner_id = partner_id

                    invoice_id = self.env['account.move'].browse(invoice_import_id.invoice_id.id)
                    invoice_id.write({
                        'invoice_line_ids': parsed_info.get('invoice_line_ids')
                    })

                    invoice_import_id.update_invoice()
            except Exception as e:
                _logger.warning("An exception occurred:", e)
        return res


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def write_message_with_attachment(self, invoices, message, attachment_filename, attachment_data):
        """This method writes a message with an attachment on an account.move record."""
        for move in invoices:
            # Create a new mail.message record
            message_values = {
                'model': move._name,
                'res_id': move.id,
                'message_type': 'comment',
                'body': message,
            }
            message = self.env['mail.message'].create(message_values)

            # Attach the file to the message
            attachment_values = {
                'name': attachment_filename,
                'res_model': move._name,
                'res_id': move.id,
                'datas': attachment_data,
            }
            attachment = self.env['ir.attachment'].create(attachment_values)

            # Link the attachment to the message
            message.attachment_ids = [(4, attachment.id)]

    def _create_invoice_from_attachment(self, attachment_ids=None):
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            raise UserError(_("No attachment was provided"))
        invoices = self.env['account.move']
        for attachment in attachments:
            invoice = False
            existing_inv = False
            try:
                invoice_import_id = self.env['account.invoice.import'].create({
                    'invoice_file': attachment.datas,
                    'invoice_filename': attachment.name,
                })
                parsed_info = invoice_import_id.get_parsed_invoice()
                existing_inv = invoice_import_id.invoice_already_exists(parsed_info["partner"]["recordset"],
                                                                        parsed_info)
                if existing_inv:
                    message = _(
                        "This invoice already exists in Odoo. It's "
                        "Supplier Invoice Number is '%s' and it's Odoo number "
                        "is '%s'"
                    ) % (parsed_info.get("invoice_number"), existing_inv.name)
                    existing_invoice = self.env['account.move'].browse(existing_inv.id)
                    self.write_message_with_attachment(existing_invoice, message, attachment.name, attachment.datas)
                    existing_invoice.to_check = True
                else:
                    invoice = invoice_import_id.create_invoice_webservice(
                        attachment.datas,
                        attachment.name,
                        origin=None,
                        company_id=None,
                        email_from=None,
                    )

            except Exception as e:
                _logger.warning("An exception occurred:", e)

            if not invoice and not existing_inv:
                invoice = super()._create_invoice_from_attachment([attachment.id]).id
            if invoice:
                _logger.warning(f"{invoice=}")
                invoices += self.env['account.move'].browse(invoice)

        _logger.warning(f"{invoices=}")
        return invoices
