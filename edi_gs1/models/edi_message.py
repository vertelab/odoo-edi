from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import logging

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _inherit = 'edi.message'

    message_reference = fields.Char(string="Message Reference", help="Reference from UNH segment")

    def _process_invoic(self):
        """Process INVOIC message and create new account.move"""
        try:
            _logger.info(f"Processing INVOIC message: {self.name}")

            # Parse the message content
            invoice_data = self._parse_invoic_data()

            # Create new invoice
            invoice = self._create_account_move(invoice_data)
            _logger.info(f"✓ Created invoice: {invoice.name}")

            return invoice

        except Exception as e:
            _logger.error(f"Failed to process INVOIC message {self.name}: {str(e)}")
            raise

    def _process_invoic_update(self, existing_invoice):
        """Update existing invoice with INVOIC message data"""
        try:
            _logger.info(f"Updating existing invoice {existing_invoice.name} with INVOIC data")

            # Parse the message content (same method as create)
            invoice_data = self._parse_invoic_data()

            # Update the existing invoice
            self._update_invoice_with_edi_data(existing_invoice, invoice_data)

            _logger.info(f"✓ Updated invoice: {existing_invoice.name}")

            return existing_invoice

        except Exception as e:
            _logger.error(f"Failed to update invoice with INVOIC message {self.name}: {str(e)}")
            raise

    def _parse_invoic_data(self):
        """Parse INVOIC message and return structured invoice data"""
        # Get message content from payload
        content = base64.b64decode(self.payload).decode('utf-8')
        _logger.info("Parsing INVOIC data from EDI content")

        # Initialize invoice data structure
        invoice_data = {
            'document_number': '',
            'date': None,
            'partner': None,
            'line_items': [],
            'currency': None  # Will be set from CUX segment or default to company currency
        }
        current_line = None

        # Segment handlers registry
        segment_handlers = {
            'BGM': self._handle_bgm_segment,
            'DTM': self._handle_dtm_segment,
            'NAD': self._handle_nad_segment,
            'CUX': self._handle_cux_segment,
            'LIN': self._handle_lin_segment,
            'IMD': self._handle_imd_segment,
            'QTY': self._handle_qty_segment,
            'PRI': self._handle_pri_segment,
            'MOA': self._handle_moa_segment,
            'TAX': self._handle_tax_segment,
            'ALC': self._handle_alc_segment,
            'RFF': self._handle_rff_segment,
            'PIA': self._handle_pia_segment,
            'PAT': self._handle_pat_segment,
            'PCD': self._handle_pcd_segment,
            'CTA': self._handle_cta_segment,
            'COM': self._handle_com_segment,
            'UNS': self._handle_uns_segment,
        }

        # Process each line
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Split by + to get elements
            elements = line.split('+')
            segment_tag = elements[0][:3]

            # Handle the segment using registry
            handler = segment_handlers.get(segment_tag)
            if handler:
                current_line = handler(elements, invoice_data, current_line)

        # Add last line item if any
        if current_line:
            invoice_data['line_items'].append(current_line)

        return invoice_data

    # Segment handler methods
    def _handle_bgm_segment(self, elements, invoice_data, current_line):
        """Handle BGM (Beginning of Message) segment"""
        # BGM+380+18871152+9
        if len(elements) > 2:
            invoice_data['document_number'] = elements[2]
            _logger.debug(f"Document number: {invoice_data['document_number']}")
        return current_line

    def _handle_dtm_segment(self, elements, invoice_data, current_line):
        """Handle DTM (Date/Time) segment"""
        # DTM+137:20170704:102
        if len(elements) > 1:
            date_parts = elements[1].split(':')
            if len(date_parts) > 1 and date_parts[0] == '137':  # Invoice date
                date_str = date_parts[1]
                if len(date_str) == 8:  # YYYYMMDD format
                    try:
                        invoice_data['date'] = datetime.strptime(date_str, '%Y%m%d').date()
                        _logger.debug(f"Invoice date: {invoice_data['date']}")
                    except ValueError:
                        _logger.warning(f"Invalid date format: {date_str}")
        return current_line

    def _handle_nad_segment(self, elements, invoice_data, current_line):
        """Handle NAD (Name and Address) segment"""
        # NAD+SU+8716106053889::9++Kramp Deutschland+Siemensstrasse 1+Strullendorf++96129+DE
        if len(elements) > 1 and elements[1] == 'SU':  # Supplier
            supplier_partner = self._create_supplier_from_nad(elements)
            if supplier_partner:
                invoice_data['partner'] = supplier_partner
                _logger.info(f"Found/created supplier: {supplier_partner.name}")
        return current_line

    def _handle_cux_segment(self, elements, invoice_data, current_line):
        """Handle CUX (Currency) segment"""
        # CUX+2:EUR:4++1
        if len(elements) > 1:
            currency_parts = elements[1].split(':')
            if len(currency_parts) > 1:
                currency_code = currency_parts[1]

                # Find currency in Odoo
                currency = self.env['res.currency'].search([
                    ('name', '=', currency_code)
                ], limit=1)

                if currency:
                    invoice_data['currency'] = currency
                    _logger.debug(f"Currency found: {currency.name}")
                else:
                    _logger.warning(f"Currency '{currency_code}' not found in system")
                    # Fallback to company currency
                    invoice_data['currency'] = self.env.company.currency_id
        return current_line

    def _handle_lin_segment(self, elements, invoice_data, current_line):
        """Handle LIN (Line Item) segment"""
        # LIN+5++100100:SA
        # Save previous line item
        if current_line:
            invoice_data['line_items'].append(current_line)

        # Start new line item
        current_line = {
            'product_code': '',
            'description': '',
            'quantity': 1.0,
            'price': 0.0
        }

        if len(elements) > 3:
            product_parts = elements[3].split(':')
            if product_parts[0]:
                current_line['product_code'] = product_parts[0]
                _logger.debug(f"New line item: {current_line['product_code']}")

        return current_line

    def _handle_imd_segment(self, elements, invoice_data, current_line):
        """Handle IMD (Item Description) segment"""
        # IMD+A++:::Crosspost 55x22 mm:100100
        if current_line and len(elements) > 3:
            desc_parts = elements[3].split(':')
            if len(desc_parts) > 3:
                current_line['description'] = desc_parts[3]
                _logger.debug(f"Description: {current_line['description']}")
        return current_line

    def _handle_qty_segment(self, elements, invoice_data, current_line):
        """Handle QTY (Quantity) segment"""
        # QTY+47:1:EA
        if current_line and len(elements) > 1:
            qty_parts = elements[1].split(':')
            if len(qty_parts) > 1:
                try:
                    current_line['quantity'] = float(qty_parts[1])
                    _logger.debug(f"Quantity: {current_line['quantity']}")
                except ValueError:
                    _logger.warning(f"Invalid quantity: {qty_parts[1]}")
        return current_line

    def _handle_pri_segment(self, elements, invoice_data, current_line):
        """Handle PRI (Price) segment"""
        # PRI+AAA:25.00:::1:EA
        if current_line and len(elements) > 1:
            price_parts = elements[1].split(':')
            if len(price_parts) > 1:
                try:
                    price_value = float(price_parts[1])
                    # Prefer net price (AAA) over gross (AAB)
                    if price_parts[0] == 'AAA' or current_line['price'] == 0.0:
                        current_line['price'] = price_value
                        _logger.debug(f"Price: {current_line['price']} ({price_parts[0]})")
                except ValueError:
                    _logger.warning(f"Invalid price: {price_parts[1]}")
        return current_line

    def _handle_moa_segment(self, elements, invoice_data, current_line):
        """Handle MOA (Monetary Amount) segment"""
        # MOA+203:4.96 or MOA+124:4.75
        # This can be line-level or document-level amounts
        # For now, we'll just log it for future enhancement
        if len(elements) > 1:
            amount_parts = elements[1].split(':')
            if len(amount_parts) > 1:
                _logger.debug(f"Monetary amount: {amount_parts[0]}:{amount_parts[1]}")
        return current_line

    def _handle_tax_segment(self, elements, invoice_data, current_line):
        """Handle TAX (Tax) segment"""
        # TAX+7+VAT+++:::19
        # For future enhancement - tax calculation
        if len(elements) > 4:
            tax_parts = elements[4].split(':')
            if len(tax_parts) > 3:
                _logger.debug(f"Tax rate: {tax_parts[3]}%")
        return current_line

    def _handle_alc_segment(self, elements, invoice_data, current_line):
        """Handle ALC (Allowance/Charge) segment"""
        # ALC+A+++1+DI:::Discount
        # For future enhancement - discounts and charges
        if len(elements) > 5:
            charge_parts = elements[5].split(':')
            if len(charge_parts) > 3:
                _logger.debug(f"Allowance/Charge: {charge_parts[3]}")
        return current_line

    def _handle_rff_segment(self, elements, invoice_data, current_line):
        """Handle RFF (Reference) segment"""
        # RFF+IV:18871152 (Invoice reference)
        # RFF+VA:DE235420954 (VAT number)
        # RFF+DQ:03382238 (Delivery quote)
        # RFF+VN:49399685:5_0 (Vendor reference)
        # RFF+ON:1529785353 (Order number)
        if len(elements) > 1:
            ref_parts = elements[1].split(':')
            if len(ref_parts) > 1:
                ref_qualifier = ref_parts[0]
                ref_number = ref_parts[1]

                # Initialize references dict if not exists
                if 'references' not in invoice_data:
                    invoice_data['references'] = {}

                invoice_data['references'][ref_qualifier] = ref_number
                _logger.debug(f"Reference {ref_qualifier}: {ref_number}")

                # Store order number for potential use
                if ref_qualifier == 'ON':  # Order number
                    invoice_data['order_reference'] = ref_number
        return current_line

    def _handle_pia_segment(self, elements, invoice_data, current_line):
        """Handle PIA (Product Identification) segment"""
        # PIA+5+100100:SA
        if current_line and len(elements) > 2:
            product_parts = elements[2].split(':')
            if product_parts[0]:
                # Store additional product identifier
                if 'alt_product_code' not in current_line:
                    current_line['alt_product_code'] = product_parts[0]
                    _logger.debug(f"Alternative product code: {current_line['alt_product_code']}")
        return current_line

    def _handle_pat_segment(self, elements, invoice_data, current_line):
        """Handle PAT (Payment Terms) segment"""
        # PAT+3 (Payment terms type)
        # PAT+22++5:3:D:8 (Discount terms)
        if len(elements) > 1:
            if 'payment_terms' not in invoice_data:
                invoice_data['payment_terms'] = {}

            payment_type = elements[1]
            invoice_data['payment_terms']['type'] = payment_type

            # Handle discount terms
            if len(elements) > 3:
                discount_parts = elements[3].split(':')
                if len(discount_parts) > 3:
                    invoice_data['payment_terms']['discount_days'] = discount_parts[1]
                    invoice_data['payment_terms']['discount_percent'] = discount_parts[0]
                    _logger.debug(f"Payment terms: {discount_parts[0]}% in {discount_parts[1]} days")
        return current_line

    def _handle_pcd_segment(self, elements, invoice_data, current_line):
        """Handle PCD (Percentage Details) segment"""
        # PCD+12:2 (Discount percentage)
        if len(elements) > 1:
            percent_parts = elements[1].split(':')
            if len(percent_parts) > 1:
                _logger.debug(f"Percentage: {percent_parts[0]}% = {percent_parts[1]}")
        return current_line

    def _handle_cta_segment(self, elements, invoice_data, current_line):
        """Handle CTA (Contact Information) segment"""
        # CTA+SU (Contact for supplier)
        if len(elements) > 1:
            _logger.debug(f"Contact type: {elements[1]}")
        return current_line

    def _handle_com_segment(self, elements, invoice_data, current_line):
        """Handle COM (Communication Contact) segment"""
        # COM+?+49 (0)9543 4430-100:TE (Phone number)
        if len(elements) > 1:
            comm_parts = elements[1].split(':')
            if len(comm_parts) > 1:
                _logger.debug(f"Communication: {comm_parts[0]} ({comm_parts[1]})")
        return current_line

    def _handle_uns_segment(self, elements, invoice_data, current_line):
        """Handle UNS (Section Control) segment"""
        # UNS+S (Summary section)
        if len(elements) > 1 and elements[1] == 'S':
            _logger.debug("Entering summary section")
            # Add current line before summary if exists
            if current_line:
                invoice_data['line_items'].append(current_line)
                current_line = None
        return current_line

    def _create_supplier_from_nad(self, nad_elements):
        """Create or find supplier partner from NAD+SU segment"""
        # NAD+SU+8716106053889::9++Kramp Deutschland+Siemensstrasse 1+Strullendorf++96129+DE

        if len(nad_elements) < 3:
            return None

        # Extract EDI code from element 2: "8716106053889::9"
        partner_parts = nad_elements[2].split(':')
        edi_code = partner_parts[0] if partner_parts[0] else None

        if not edi_code:
            return None

        # Try to find existing partner
        partner = self.env['res.partner'].search([
            ('edi_code', '=', edi_code)
        ], limit=1)

        if partner:
            _logger.info(f"Found existing supplier partner: {partner.name}")
            return partner

        # Extract address information
        partner_data = {
            'edi_code': edi_code,
            'is_company': True,
            'supplier_rank': 1,
        }

        # Element 4: Company name
        if len(nad_elements) > 4 and nad_elements[4]:
            partner_data['name'] = nad_elements[4]
        else:
            partner_data['name'] = f'Supplier {edi_code}'

        # Element 5: Street
        if len(nad_elements) > 5 and nad_elements[5]:
            partner_data['street'] = nad_elements[5]

        # Element 6: City
        if len(nad_elements) > 6 and nad_elements[6]:
            partner_data['city'] = nad_elements[6]

        # Element 8: Postal code (element 7 is usually empty)
        if len(nad_elements) > 8 and nad_elements[8]:
            partner_data['zip'] = nad_elements[8]

        # Element 9: Country code
        if len(nad_elements) > 9 and nad_elements[9]:
            country = self.env['res.country'].search([
                ('code', '=', nad_elements[9])
            ], limit=1)
            if country:
                partner_data['country_id'] = country.id

        # Create the partner
        partner = self.env['res.partner'].create(partner_data)
        _logger.info(f"Created new supplier partner: {partner.name} (EDI: {edi_code})")

        return partner

    def _create_account_move(self, invoice_data):
        """Create new account.move from parsed data"""
        # Get currency - use parsed currency or fall back to company currency
        currency = invoice_data.get('currency') or self.env.company.currency_id

        # Use partner from invoice data or envelope sender
        partner = invoice_data['partner'] or self.envelope_id.sender

        if not partner:
            raise ValidationError(_('No partner found for invoice'))

        # Prepare invoice data
        move_vals = {
            'move_type': 'in_invoice',  # Vendor bill
            'partner_id': partner.id,
            'invoice_date': invoice_data['date'] or fields.Date.today(),
            'ref': invoice_data['document_number'],
            'currency_id': currency.id,
            'invoice_line_ids': []
        }

        # Create invoice lines
        for line_data in invoice_data['line_items']:
            if line_data['quantity'] > 0 and line_data['price'] > 0:
                # Find or create product
                product = self._find_or_create_product(line_data)

                line_vals = {
                    'product_id': product.id if product else False,
                    'name': line_data['description'] or 'EDI Product',
                    'quantity': line_data['quantity'],
                    'price_unit': line_data['price'],
                }
                move_vals['invoice_line_ids'].append((0, 0, line_vals))

        if not move_vals['invoice_line_ids']:
            raise ValidationError(_('No valid invoice lines found'))

        # Create the invoice
        invoice = self.env['account.move'].create(move_vals)

        # Link to this message
        invoice.message_post(body=f"Created from EDI message: {self.name}")

        return invoice

    def _update_invoice_with_edi_data(self, invoice, invoice_data):
        """Update existing invoice with parsed EDI data"""
        # Update header fields
        update_vals = {}

        if invoice_data['document_number']:
            update_vals['ref'] = invoice_data['document_number']

        if invoice_data['date']:
            update_vals['invoice_date'] = invoice_data['date']

        if invoice_data['partner']:
            update_vals['partner_id'] = invoice_data['partner'].id

        # Set currency - use parsed currency or keep existing
        currency = invoice_data.get('currency')
        if currency:
            update_vals['currency_id'] = currency.id

        # Clear existing lines and add EDI lines
        invoice.invoice_line_ids.unlink()

        line_vals = []
        for line_data in invoice_data['line_items']:
            if line_data['quantity'] > 0 and line_data['price'] > 0:
                # Find or create product
                product = self._find_or_create_product(line_data)

                line_vals.append((0, 0, {
                    'product_id': product.id if product else False,
                    'name': line_data['description'] or 'EDI Product',
                    'quantity': line_data['quantity'],
                    'price_unit': line_data['price'],
                }))

        update_vals['invoice_line_ids'] = line_vals

        # Update the invoice
        invoice.write(update_vals)

        # Add message
        invoice.message_post(body=f"Updated with EDI data from message: {self.name}")

        _logger.info(f"Updated invoice {invoice.name} with {len(line_vals)} EDI lines")

    def _find_or_create_product(self, line_data):
        """Find existing product or create new one"""
        product_code = line_data['product_code']

        if product_code:
            # Try to find by default_code
            product = self.env['product.product'].search([
                ('default_code', '=', product_code)
            ], limit=1)

            if product:
                _logger.debug(f"Found existing product: {product.name}")
                return product

        # Create new product
        product_vals = {
            'name': line_data['description'] or f'EDI Product {product_code}',
            'default_code': product_code,
            'type': 'consu',  # Consumable
            'purchase_ok': True,
            'sale_ok': True,
        }

        product = self.env['product.product'].create(product_vals)
        _logger.info(f"Created new product: {product.name}")

        return product

    def unpack(self):
        """Override unpack method to handle EDIFACT parsing"""
        message_type = self.message_format_id.name.split(':')[0] if self.message_format_id else ''

        if message_type == 'INVOIC':
            return self._process_invoic()
        elif message_type == 'ORDERS':
            # TODO: Implement ORDERS processing using same registry pattern
            _logger.info(f"ORDERS processing not yet implemented for {self.name}")
        else:
            _logger.info(f"Generic processing not yet implemented for {self.name}")
        return True

    @api.model
    def pack(self, rec=None):
        """Pack Odoo record into EDI message"""
        if not rec:
            raise ValidationError(_('No record provided for packing'))

        _logger.info(f"Packing {rec._name} {rec.id} into EDI message")

        # Route to appropriate packing method based on model
        if rec._name == 'account.move':
            return self._pack_account_move(rec)

        else:
            raise ValidationError(_('Packing not supported for model: %s') % rec._name)

    def _pack_account_move(self, invoice):
        """Pack account.move (invoice) into EDIFACT INVOIC message"""
        # Validate invoice
        # if invoice.move_type not in ['out_invoice', 'out_refund']:
        #     raise ValidationError(_('Only customer invoices and credit notes can be packed'))

        if not invoice.partner_id.edi_code:
            raise ValidationError(_('Customer %s does not have an EDI code') % invoice.partner_id.name)

        # Create or find envelope for this partner
        envelope = self._get_or_create_envelope_for_partner(
            sender=self.env.company.partner_id,
            receiver=invoice.partner_id
        )

        print("envelope", envelope)

        # Create EDI message
        message_type = 'INVOIC'
        message_format = self._get_or_create_message_format(message_type, 'D', '96A')
        message_ref = invoice.name.replace('/', '_')

        message = self.create({
            'name': f"{message_type} {message_ref}",
            'message_format_id': message_format.id,
            'envelope_id': envelope.id,
            'sender': envelope.sender.id,
            'receiver': envelope.receiver.id,
            'message_reference': message_ref,
        })

        # Generate EDIFACT content
        content = message._generate_invoic_content(invoice)
        message.payload = base64.b64encode(content.encode('utf-8'))
        message.payload_filename = f"{message.name}.edi"

        _logger.info(f"✓ Packed invoice {invoice.name} into EDI message {message.name}")

        return message

    def _generate_invoic_content(self, invoice):
        """Generate EDIFACT INVOIC content from Odoo invoice"""
        segments = []

        # UNH - Message Header
        segments.append(f"UNH+{self.message_reference}+INVOIC:D:96A:UN'")

        # BGM - Beginning of Message
        doc_code = '380' if invoice.move_type == 'out_invoice' else '381'  # 381 for credit note
        segments.append(f"BGM+{doc_code}+{invoice.name}+9'")

        # DTM - Date/Time (Invoice Date)
        if invoice.invoice_date:
            date_str = invoice.invoice_date.strftime('%Y%m%d')
            segments.append(f"DTM+137:{date_str}:102'")

        # RFF - Reference (Customer Reference)
        if invoice.ref:
            segments.append(f"RFF+CR:{invoice.ref}'")

        # NAD - Name and Address (Seller - us)
        company_partner = self.env.company.partner_id
        if company_partner.edi_code:
            segments.append(self._generate_nad_segment('SE', company_partner))

        # NAD - Name and Address (Buyer - customer)
        if invoice.partner_id.edi_code:
            segments.append(self._generate_nad_segment('BY', invoice.partner_id))

        # CUX - Currency
        segments.append(f"CUX+2:{invoice.currency_id.name}:4++1'")

        # PAT - Payment Terms (if available)
        if invoice.invoice_payment_term_id:
            segments.append(f"PAT+1'")
            # Could add more detailed payment terms here

        # Line Items
        line_count = 0
        for line in invoice.invoice_line_ids:
            if line.display_type in ('line_section', 'line_note'):
                continue  # Skip section and note lines

            line_count += 1

            # LIN - Line Item
            product_code = line.product_id.default_code or line.product_id.barcode or str(line.product_id.id)
            segments.append(f"LIN+{line_count}++{product_code}:SA'")

            # PIA - Additional Product Identification (if available)
            if line.product_id.barcode and line.product_id.barcode != product_code:
                segments.append(f"PIA+1+{line.product_id.barcode}:EN'")

            # IMD - Item Description
            description = self._clean_edi_text(line.name or line.product_id.name)
            segments.append(f"IMD+A++:::{description}'")

            # QTY - Quantity
            uom_code = line.product_uom_id.name[:3].upper() if line.product_uom_id else 'EA'
            segments.append(f"QTY+47:{line.quantity}:{uom_code}'")

            # PRI - Price (Net unit price)
            segments.append(f"PRI+AAA:{line.price_unit}:::1:{uom_code}'")

            # MOA - Line Amount
            segments.append(f"MOA+203:{line.price_subtotal}'")

            # TAX - Tax Information (if tax applied)
            if line.tax_ids:
                tax_rate = sum(line.tax_ids.mapped('amount'))
                segments.append(f"TAX+7+VAT+++::::{tax_rate}'")

        # UNS - Section Control (Summary section)
        segments.append("UNS+S'")

        # Summary MOA segments
        segments.append(f"MOA+79:{invoice.amount_untaxed}'")  # Net amount
        segments.append(f"MOA+176:{invoice.amount_tax}'")  # Tax amount
        segments.append(f"MOA+128:{invoice.amount_total}'")  # Total amount

        # Summary TAX segment
        if invoice.amount_tax > 0:
            # Calculate average tax rate
            tax_rate = (invoice.amount_tax / invoice.amount_untaxed * 100) if invoice.amount_untaxed > 0 else 0
            segments.append(f"TAX+7+VAT+++::::{tax_rate:.2f}'")
            segments.append(f"MOA+124:{invoice.amount_tax}'")  # Tax amount

        # UNT - Message Trailer
        segments.append(f"UNT+{len(segments) + 1}+{self.message_reference}'")

        content = '\n'.join(segments)
        _logger.info(f"Generated INVOIC content with {len(segments)} segments")

        return content

    def _generate_nad_segment(self, qualifier, partner):
        """Generate NAD segment for partner"""
        # Clean text fields for EDI format
        name = self._clean_edi_text(partner.name)
        street = self._clean_edi_text(partner.street or '')
        city = self._clean_edi_text(partner.city or '')

        return (f"NAD+{qualifier}+{partner.edi_code or ''}::9++"
                f"{name}+{street}+{city}++{partner.zip or ''}+"
                f"{partner.country_id.code or ''}'")

    def _clean_edi_text(self, text):
        """Clean text for EDI format - remove problematic characters"""
        if not text:
            return ''

        # Remove or replace characters that could break EDI format
        text = str(text)
        text = text.replace("'", "")  # Remove single quotes (segment terminator)
        text = text.replace("+", "")  # Remove plus signs (element separator)
        text = text.replace(":", "")  # Remove colons (component separator)
        text = text.replace("?", "")  # Remove question marks (escape character)
        text = text.replace("\n", " ")  # Replace newlines with spaces
        text = text.replace("\r", "")  # Remove carriage returns

        # Limit length to reasonable EDI field size
        return text[:70]

    def _get_or_create_envelope_for_partner(self, sender, receiver):
        """Get existing envelope or create new one for partner communication"""
        # Look for existing envelope in draft state for same direction
        # envelope = self.env['edi.envelope'].search([
        #     ('sender', '=', sender.id),
        #     ('receiver', '=', receiver.id),
        #     ('state', '=', 'to_be_sent'),
        #     ('type', '=', 'gs1')
        # ], limit=1)
        #
        # if envelope:
        #     _logger.info(f"Using existing envelope {envelope.name}")
        #     return envelope

        # Create new envelope
        envelope = self.env['edi.envelope'].create({
            'name': f"EDI Export {receiver.name} {fields.Datetime.now().strftime('%Y%m%d_%H%M')}",
            'sender': sender.id,
            'receiver': receiver.id,
            'type': 'gs1',
            'state': 'to_be_sent',
        })

        _logger.info(f"Created new envelope {envelope.name}")
        return envelope

    def _get_or_create_message_format(self, msg_type, version, release):
        """Find or create edi.message.format record"""
        format_name = f"{msg_type}:{version}:{release}"

        message_format = self.env['edi.message.format'].search([
            ('name', '=', format_name)
        ], limit=1)

        if not message_format:
            message_format = self.env['edi.message.format'].create({
                'name': format_name,
            })

        return message_format