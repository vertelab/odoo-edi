from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import logging

try:
    from pydifact.segmentcollection import Interchange
except ImportError:
    Interchange = None

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _create_document_from_attachment(self, attachment_ids):
        """Override to handle EDI files after standard processing"""
        # First, let standard processing create basic invoices
        invoices = super()._create_document_from_attachment(attachment_ids)

        if not Interchange:
            _logger.warning("pydifact library not available, skipping EDI processing")
            return invoices

        # Process EDI files and update the created invoices
        for attachment in self.env['ir.attachment'].browse(attachment_ids):
            if self._is_edifact_file(attachment):
                try:
                    _logger.info(f"Processing EDI file: {attachment.name}")

                    # Find the invoice created for this attachment
                    invoice = invoices.filtered(
                        lambda inv: attachment.id in inv.message_ids.mapped('attachment_ids').ids)
                    if not invoice:
                        # Alternative: find by attachment res_id
                        invoice = invoices.filtered(lambda inv: inv.id == attachment.res_id)

                    if invoice:
                        _logger.info(f"Found invoice {invoice.name} for EDI processing")

                        # Create envelope and update the existing invoice
                        envelope = self.env['edi.envelope'].create_from_edifact_attachment(attachment, invoice)
                        _logger.info(f"✓ Created envelope: {envelope.name}")

                    else:
                        _logger.warning(f"No invoice found for EDI attachment {attachment.name}")

                except Exception as e:
                    _logger.error(f"Failed to process EDI attachment {attachment.name}: {str(e)}")
                    # Don't raise error - let the basic invoice remain
                    _logger.error(f"EDI processing failed, keeping basic invoice")

        return invoices

    def _is_edifact_file(self, attachment):
        """Check if attachment is an EDIFACT file"""
        if not attachment.datas or not Interchange:
            return False

        try:
            content = base64.b64decode(attachment.datas).decode('utf-8')

            # Simple check for EDIFACT markers
            if not any(marker in content for marker in ['UNA', 'UNB+', 'UNH+']):
                return False

            # Try to parse with pydifact
            interchange = Interchange.from_str(content)
            messages = list(interchange.get_messages())

            _logger.info(f"EDIFACT validation: {len(messages)} messages found")
            return len(messages) > 0

        except Exception as e:
            _logger.debug(f"File {attachment.name} failed EDIFACT validation: {str(e)}")
            return False