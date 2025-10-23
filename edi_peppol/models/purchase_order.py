# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    issue_date = fields.Datetime(string="Issue Date")
    validity_period = fields.Datetime(string="Validity Period")

    show_send_peppol_button = fields.Boolean(compute="compute_show_send_peppol_button", store=False) #compute="compute_show_send_peppol_button"

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
                

    

            
   