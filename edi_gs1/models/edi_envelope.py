from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import logging

try:
    from pydifact.segmentcollection import Interchange
except ImportError:
    raise ImportError("pydifact library is required. Install with: pip install pydifact")

_logger = logging.getLogger(__name__)


class EdiEnvelope(models.Model):
    _inherit = 'edi.envelope'

    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    # Add EDI-specific fields
    interchange_control_reference = fields.Char(string="Control Reference")
    syntax_identifier = fields.Char(string="Syntax Identifier")
    reference = fields.Reference(string='Reference', selection='_selection_target_model')


    @api.model
    def create_from_edifact_attachment(self, attachment, existing_invoice=None):
        """Create envelope from EDIFACT attachment and automatically process it"""
        try:
            # Decode attachment content
            content = base64.b64decode(attachment.datas).decode('utf-8')
            _logger.info(f"Creating envelope from EDIFACT attachment: {attachment.name}")

            # Parse with pydifact first to validate
            interchange = Interchange.from_str(content)
            messages = list(interchange.get_messages())
            _logger.info(f"✓ Validated EDIFACT: {len(messages)} messages found")

            # Extract envelope info from UNB line in raw content
            sender_id = ""
            receiver_id = ""
            control_ref = ""
            syntax_id = ""

            # Parse UNB line manually from content
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('UNB+'):
                    # UNB+UNOC:3+8716106053841:14+9999999999994:14+180914:1530+3
                    elements = line.split('+')
                    if len(elements) >= 5:
                        syntax_id = elements[1]
                        sender_id = elements[2]
                        receiver_id = elements[3]
                        # Control reference might be in element 4 or 5
                        datetime_part = elements[4]
                        control_ref = elements[5] if len(elements) > 5 else datetime_part.split(':')[0]
                    break

            _logger.info(f"✓ Extracted envelope: Sender={sender_id}, Receiver={receiver_id}, Control={control_ref}")

            # If we couldn't parse UNB, create with minimal info
            if not sender_id and not receiver_id:
                _logger.warning("Could not extract UNB info, creating envelope with attachment name")
                sender_id = "UNKNOWN_SENDER"
                receiver_id = "UNKNOWN_RECEIVER"
                control_ref = attachment.name

            # Resolve or create partners
            sender = self._resolve_or_create_partner(sender_id)
            receiver = self._resolve_or_create_partner(receiver_id)

            # Create envelope
            envelope = self.create({
                'name': f"EDI {control_ref or attachment.name}",
                'sender': sender.id if sender else False,
                'receiver': receiver.id if receiver else False,
                'payload': attachment.datas,
                'payload_filename': attachment.name,
                'type': 'gs1',
                'state': 'received',
                'interchange_control_reference': control_ref,
                'syntax_identifier': syntax_id,
                'reference': f'{existing_invoice._name},{existing_invoice.id}'
            })

            # Automatically process the envelope (with existing invoice if provided)
            envelope.unfold(existing_invoice)

            return envelope

        except Exception as e:
            _logger.error(f"Error in create_from_edifact_attachment: {str(e)}", exc_info=True)
            raise ValidationError(_('Failed to create envelope from EDI file: %s') % str(e))

    def unfold(self, existing_invoice=None):
        """Process the envelope and create messages"""
        result = super().unfold()
        try:
            content = base64.b64decode(self.payload).decode('utf-8')
            interchange = Interchange.from_str(content)

            messages = list(interchange.get_messages())
            _logger.info(f"Processing envelope {self.name} with {len(messages)} messages")

            # Parse UNH segments manually from raw content since pydifact excludes them from message.segments
            unh_segments = []
            message_contents = []

            # Split content into individual messages
            lines = content.split('\n')
            current_message_lines = []
            in_message = False

            for line in lines:
                line = line.strip()

                if line.startswith('UNH+'):
                    # Start of new message
                    if current_message_lines:
                        # Save previous message
                        message_contents.append('\n'.join(current_message_lines))

                    # Parse UNH+3+INVOIC:D:96A:UN'
                    elements = line.split('+')
                    unh_data = {
                        'reference': elements[1] if len(elements) > 1 else '',
                        'type_info': elements[2] if len(elements) > 2 else ''
                    }
                    unh_segments.append(unh_data)
                    current_message_lines = [line]  # Start with UNH
                    in_message = True
                    _logger.info(f"Found UNH: {unh_data}")

                elif line.startswith('UNT+'):
                    # End of message
                    if in_message:
                        current_message_lines.append(line)  # Include UNT
                        message_contents.append('\n'.join(current_message_lines))
                        current_message_lines = []
                        in_message = False

                elif in_message and not line.startswith(('UNB+', 'UNZ+')):
                    # Message content (exclude envelope segments)
                    current_message_lines.append(line)

            # Add last message if any
            if current_message_lines:
                message_contents.append('\n'.join(current_message_lines))

            _logger.info(f"Extracted {len(message_contents)} individual message payloads")

            # Create messages with individual payloads
            for i, (unh_data, message_content) in enumerate(zip(unh_segments, message_contents)):
                pydifact_message = messages[i] if i < len(messages) else None
                edi_message = self._create_message_with_payload(unh_data, message_content, pydifact_message)
                _logger.info(f"✓ Created message: {edi_message.name} with {len(message_content)} chars payload")

                # Automatically process INVOIC messages
                if edi_message.message_format_id.name.startswith('INVOIC'):
                    if existing_invoice:
                        _logger.info(f"Updating existing invoice {existing_invoice.name} with EDI data")
                        edi_message._process_invoic_update(existing_invoice)
                    else:
                        edi_message._process_invoic()

        except Exception as e:
            self.state = 'error'
            _logger.error(f"Failed to process envelope {self.name}: {str(e)}")
            raise
        return result

    def _create_message_with_payload(self, unh_data, message_content, pydifact_message):
        """Create edi.message with individual message payload"""
        import base64

        # Parse message type info from UNH: INVOIC:D:96A:UN
        message_reference = unh_data['reference']
        type_parts = unh_data['type_info'].split(':')

        message_type = type_parts[0] if len(type_parts) > 0 else 'UNKNOWN'
        version = type_parts[1] if len(type_parts) > 1 else ''
        release = type_parts[2] if len(type_parts) > 2 else ''

        _logger.info(f"Creating message: {message_type} {message_reference}, version: {version}, release: {release}")

        # Find or create message format
        message_format = self._get_or_create_message_format(message_type, version, release)

        # Encode individual message content
        message_payload = base64.b64encode(message_content.encode('utf-8'))

        edi_message = self.env['edi.message'].create({
            'name': f"{message_type} {message_reference}",
            'message_format_id': message_format.id,
            'envelope_id': self.id,
            'sender': self.sender.id,
            'receiver': self.receiver.id,
            'payload': message_payload,  # Individual message content only
            'payload_filename': f"{message_type}_{message_reference}.edi",
        })

        return edi_message

    def _resolve_or_create_partner(self, edi_code_with_qualifier):
        """Resolve partner from EDI code or create new one"""
        if not edi_code_with_qualifier:
            return None

        # Extract code (remove qualifier like :14)
        edi_code = edi_code_with_qualifier.split(':')[0]

        # Try to find existing partner
        partner = self.env['res.partner'].search([
            ('edi_code', '=', edi_code)
        ], limit=1)

        if partner:
            return partner

        # Create new partner
        partner = self.env['res.partner'].create({
            'name': f'EDI Partner {edi_code}',
            'edi_code': edi_code,
            'is_company': True,
            'supplier_rank': 1,
        })

        _logger.info(f"Created new partner from EDI code: {edi_code}")
        return partner

    def _create_edi_message_from_pydifact(self, message):
        """Create edi.message record from pydifact message"""
        # Extract message header info
        unh_segment = None
        for segment in message.segments:
            if segment.tag == 'UNH':
                unh_segment = segment
                break

        if not unh_segment:
            raise ValidationError(_('No UNH segment found in message'))

        # Parse message type info (e.g., ['INVOIC', 'D', '96A', 'UN'])
        message_reference = unh_segment.elements[0] if len(unh_segment.elements) > 0 else ''
        message_type_info = unh_segment.elements[1] if len(unh_segment.elements) > 1 else []

        if isinstance(message_type_info, list):
            message_type = message_type_info[0] if len(message_type_info) > 0 else 'UNKNOWN'
            version = message_type_info[1] if len(message_type_info) > 1 else ''
            release = message_type_info[2] if len(message_type_info) > 2 else ''
        else:
            # Fallback if it's a string
            parts = str(message_type_info).split(':')
            message_type = parts[0] if len(parts) > 0 else 'UNKNOWN'
            version = parts[1] if len(parts) > 1 else ''
            release = parts[2] if len(parts) > 2 else ''

        # Find or create message format
        message_format = self._get_or_create_message_format(message_type, version, release)

        message_record = self.env['edi.message'].create({
            'name': f"{message_type} {message_reference}",
            'message_format_id': message_format.id,
            'envelope_id': self.id,
            'sender': self.sender.id,
            'receiver': self.receiver.id,
            'payload': self.payload,
            'payload_filename': f"{message_type}_{message_reference}.edi",
        })

        return message_record

    def _get_or_create_message_format(self, msg_type, version, release):
        """Find or create edi.message.format record"""
        format_name = f"{msg_type}:{version}:{release}"

        message_format = self.env['edi.message.format'].search([
            ('name', '=', format_name)
        ], limit=1)

        if not message_format:
            message_format = self.env['edi.message.format'].create({
                'name': format_name,
                # Add other format-specific fields as needed
            })

        return message_format

    def process_to_invoices(self):
        """Process all messages in envelope and create appropriate Odoo records"""
        created_records = []

        for message in self.message_ids:
            if message.message_format_id.name.startswith('INVOIC'):
                invoice = self._process_invoic_message(message)
                if invoice:
                    created_records.append(invoice)

        return created_records

    def _process_invoic_message(self, message):
        """Process INVOIC message and create account.move using pydifact"""
        try:
            # Delegate to invoice processor service
            processor = self.env['edi.invoice.processor']
            return processor.create_invoice_from_message(self, message)

        except Exception as e:
            _logger.error(f"Failed to process INVOIC message: {str(e)}")
            raise ValidationError(_('Failed to process INVOIC message: %s') % str(e))