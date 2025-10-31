# -*- coding: utf-8 -*-
import logging
import base64
from datetime import datetime

from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    issue_date = fields.Datetime(string="Issue Date")
    validity_period = fields.Datetime(string="Validity Period")
    customer_partner_id = fields.Many2one('res.partner')
    show_send_peppol_button = fields.Boolean(compute="compute_show_send_peppol_button", store=False) #compute="compute_show_send_peppol_button"
    peppol_order_reference = fields.Char(string="Peppol Order Ref")

    def compute_show_send_peppol_button(self):
        for purchase_order in self:
            purchase_order.show_send_peppol_button = False
            if purchase_order.partner_id and purchase_order.partner_id.route_id.route_type == "BIS Ordering 3.3 Outgoing":
                route_line_id = self.env['edi.route.line'].search([('route_id','=',purchase_order.partner_id.route_id.id),('message_format_id.name','=','urn:fdc:peppol.eu:poacc:trns:order:3')])
                domain = safe_eval(route_line_id.domain)
                domain.append(('id','=',purchase_order.id))
                _logger.error(f"{domain=}")
                if self.env['purchase.order'].search(domain):
                   purchase_order.show_send_peppol_button = True

    def send_peppol_outgoing_message(self):
        for purchase_order in self:
            if purchase_order.partner_id and purchase_order.partner_id.route_id.route_type == "BIS Ordering 3.3 Outgoing":
                route_line_id = self.env['edi.route.line'].search([('route_id','=',purchase_order.partner_id.route_id.id),('message_format_id.name','=','urn:fdc:peppol.eu:poacc:trns:order:3')])
                ##Create an edi.session
                session_id = purchase_order.partner_id.route_id.create_edi_session()
                session_id.name = f'{purchase_order.name}'
                session_id.sessions_line_ids[0].odoo_reference = f"purchase.order,{purchase_order.id}"
                edi_message = session_id.sessions_line_ids[0].pack()

                edi_envelope = self.env['edi.envelope'].create({
                    # 'message_ids': [(6,0, [edi_message.id])],
                    'sender': edi_message.sender.id,
                    'reciever': edi_message.reciever.id,
                    'payload': edi_message.payload,
                    'payload_filename':edi_message.payload_filename,
                    'state': 'to_be_sent',
                    'type': 'peppol'
                })

                edi_message.envelope_id = edi_envelope.id

                edi_envelope.name = f'Envelope {edi_envelope.id}'
                edi_envelope.transport_id = session_id.sessions_line_ids[0].transport_id.id


    @api.depends('name')
    def _compute_edi_messages(self):
        for rec in self:
            edi_messages = self.env['edi.message'].search([
                ('res_id', '=', rec.id), ('res_model', '=', 'purchase.order')])
            if edi_messages:
                rec.edi_message_ids = edi_messages.ids
                rec.edi_message_count = len(edi_messages)
            else:
                rec.edi_message_ids = False
                rec.edi_message_count = False

    edi_message_ids = fields.One2many(comodel_name='edi.message', compute=_compute_edi_messages)
    edi_message_count = fields.Integer(compute=_compute_edi_messages)

    def action_view_edi_messages(self):
        return {
            'name': _('EDI Messages'),
            'type': 'ir.actions.act_window',
            'res_model': 'edi.message',
            'view_mode': 'list,form',
            'domain': [
                ('res_id', '=', self.id),
                ('res_model', '=', 'purchase.order')
            ],
        }

    # def button_confirm(self):
    #     res = super().button_confirm()
    #     self._generate_order_response()
    #     return res

    def _generate_order_response(self):
        """Generate PEPPOL Order Response XML"""
        from datetime import datetime
        import base64

        # Get current datetime
        now = datetime.now()
        issue_date = now.strftime('%Y-%m-%d')
        issue_time = now.strftime('%H:%M:%S')

        # Build the XML
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
    <OrderResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2"
                   xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                   xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
        <cbc:CustomizationID>urn:fdc:peppol.eu:poacc:trns:order_response:3</cbc:CustomizationID>
        <cbc:ProfileID>urn:fdc:peppol.eu:poacc:bis:ordering:3</cbc:ProfileID>
        <cbc:ID>{self.name}</cbc:ID>
        <cbc:SalesOrderID>{self.name}</cbc:SalesOrderID>
        <cbc:IssueDate>{issue_date}</cbc:IssueDate>
        <cbc:IssueTime>{issue_time}</cbc:IssueTime>
        <cbc:OrderResponseCode>AP</cbc:OrderResponseCode>
        <cbc:Note>Order confirmed</cbc:Note>
        <cbc:DocumentCurrencyCode>{self.currency_id.name or 'EUR'}</cbc:DocumentCurrencyCode>
        <cbc:CustomerReference>{self.partner_ref or ''}</cbc:CustomerReference>
        <cac:OrderReference>
            <cbc:ID>{self.partner_ref or self.name}</cbc:ID>
        </cac:OrderReference>
        <cac:SellerSupplierParty>
            <cac:Party>
                <cbc:EndpointID schemeID="0088">{self.partner_id.vat or ''}</cbc:EndpointID>
                <cac:PartyIdentification>
                    <cbc:ID schemeID="0184">{self.partner_id.vat or ''}</cbc:ID>
                </cac:PartyIdentification>
                <cac:PartyLegalEntity>
                    <cbc:RegistrationName>{self.partner_id.name}</cbc:RegistrationName>
                </cac:PartyLegalEntity>
            </cac:Party>
        </cac:SellerSupplierParty>
        <cac:BuyerCustomerParty>
            <cac:Party>
                <cbc:EndpointID schemeID="0088">{self.company_id.vat or ''}</cbc:EndpointID>
                <cac:PartyIdentification>
                    <cbc:ID schemeID="0184">{self.company_id.vat or ''}</cbc:ID>
                </cac:PartyIdentification>
                <cac:PartyLegalEntity>
                    <cbc:RegistrationName>{self.company_id.name}</cbc:RegistrationName>
                </cac:PartyLegalEntity>
            </cac:Party>
        </cac:BuyerCustomerParty>'''

        # Add delivery information if date_planned exists
        if self.date_planned:
            planned_date = self.date_planned.strftime('%Y-%m-%d')
            xml_content += f'''
        <cac:Delivery>
            <cac:PromisedDeliveryPeriod>
                <cbc:StartDate>{planned_date}</cbc:StartDate>
                <cbc:EndDate>{planned_date}</cbc:EndDate>
            </cac:PromisedDeliveryPeriod>
        </cac:Delivery>'''

        # Add order lines
        for line in self.order_line:
            xml_content += f'''
        <cac:OrderLine>
            <cac:LineItem>
                <cbc:ID>{line.id}</cbc:ID>
                <cbc:LineStatusCode>5</cbc:LineStatusCode>
                <cbc:Quantity unitCode="C62">{line.product_qty}</cbc:Quantity>
                <cac:Price>
                    <cbc:PriceAmount currencyID="{self.currency_id.name or 'EUR'}">{line.price_unit}</cbc:PriceAmount>
                    <cbc:BaseQuantity unitCode="C62">1</cbc:BaseQuantity>
                </cac:Price>
                <cac:Item>
                    <cbc:Name>{line.product_id.name}</cbc:Name>
                    <cac:SellersItemIdentification>
                        <cbc:ID>{line.product_id.default_code or line.product_id.id}</cbc:ID>
                    </cac:SellersItemIdentification>
                </cac:Item>
            </cac:LineItem>
            <cac:OrderLineReference>
                <cbc:LineID>{line.id}</cbc:LineID>
            </cac:OrderLineReference>
        </cac:OrderLine>'''

        xml_content += '''
    </OrderResponse>'''

        # Create EDI message
        edi_message = self.env['edi.message'].create({
            'name': f'OrderResponse_{self.name}',
            'message_format_id': self.env.ref('edi_peppol.edi_message_format_peppol_order_response').id,
            # Update with your format ID
            'payload': base64.b64encode(xml_content.encode('utf-8')),
            'payload_filename': f'OrderResponse_{self.name}.xml',
            'consignor': self.partner_id.id,
            'consignee': self.company_id.partner_id.id,
            'sender': self.partner_id.id,
            'receiver': self.company_id.partner_id.id,
            'res_id': self.id,
            'res_model': 'purchase.order',
        })

        return edi_message


class PurchaseLine(models.Model):
    _inherit = 'purchase.order.line'

    edi_state = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('changed', 'Changed'),
        ('rejected', 'Rejected')],
        default='pending', string="EDI State")
