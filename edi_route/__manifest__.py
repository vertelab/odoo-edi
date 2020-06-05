# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'EDI Routes',
    'version': '0.1',
    'category': 'edi',
    'summary': 'Routes for EDI',
    'licence': 'AGPL-3',
    'description': """
Add generic routes,envelopes and messages for EDI usage.
Other modules will extend these classes with communication protocols,
edi-message formats and mapping to Odoo-classes. Examples of mapping
to odoo-classes: edi_route_sale, edi_route_stock;
communication protocols: edi_route_ftp (ftp/sftp) edi_route_mail;
edi-message-formats: edi_gs1, edi_peppol

 +---------------------------+---------------------------------+
 | edi.route                 | Recieves and sends envelopes    |
 |                           | using a communication protocol. |
 |                           | Route is also responsible to run|
 |                           | the edi-flow.                   |
 +---------------------------+---------------------------------+
 | edi.route.caller          | Name of contexts that can       |
 |                           | trigger actions (creation of    |
 |                           | edi-message)                    |
 +---------------------------+---------------------------------+
 | edi.envelope              | Package of one or many messages |
 |                           | organized in a format, with the |
 |                           | ability to split in messages    |
 |                           | or fold messages and pass on to |
 |                           | a route.                        |
 +---------------------------+---------------------------------+
 | edi.message               | Message in a certain format with|
 |                           | the ability to pack or unpack   |
 |                           | and map to odoo-classes         |
 +---------------------------+---------------------------------+
 | edi.application.line      | Interchange Control Ref in some |
 |                           | Envelope types. Tied to a       |
 |                           | Recipient.                      |
 +---------------------------+---------------------------------+

edi.route uses automation (ir.cron) to empty the mailbox when
recieving envelopes (edi-messages). Outgoing transfer initiates
when edi.route finds ready edi.messages (to be folded in an
edi.envelope) for its route. Every run identifies with an internal
sequence number.

Edi.route is also responsible for initiating creation of out-going
messages and actions for incomming messsages. In the (for instance)
order-workflow edi.route is asked if there is actions to do. There
is a "context" defined by edi.route.lines that represents a stage in
the workflow. For instance sale.order.action_invoice_create
(the method action_invoice_create in sale.order class). Edi.route have
rules to check if there is anything to do. Its possible to define rules
for example ESAP20 edi-flow (edi_gs1). Edi.route.caller holds a list of
all possible contexts for edi-actions.

Every envelope created internally identifies with an internal
sequence number. Incomming envelops identifies by identification given
by the part.

Each edi.message created internally identifies with an internal
sequence number. Incomming messages is identified by idenfication given
by the part. Edi-type and Consignee are keys to find a proper route for
outgoing messages.

How to connect a context (edi.route.caller) to a message
========================================================

    edi_route_sale:
    <record model="edi.route.caller" id="edi_route_sale.caller_create">
        <field name="name">sale.order.create</field>
    </record>

    @api.model
    def create(self, vals):  # Overrides sale.order.create()
        order =  super(sale_order,self).create(vals)
        if order:
            order.route_id.edi_action('sale.order.create',order=order)
        return order

    edi_gs1:
    <record model="edi.route.line" id="route_esap20_ordrsp">
        <field name="name">ESAP20 ORDRSP</field>
        <field name="caller_id" ref="edi_route_sale.caller_create"/>
        <field name="route_id" ref="edi_gs1.route_esap20"/>
        <field name="code">order._edi_message_create('edi_gs1.edi_message_type_ordrsp')</field>
    </record>

    edi_gs1/messages/ordrsp.py:

    class edi_message(models.Model):
        _inherit='edi.message'

        @api.one
        def _pack(self):
            super(edi_message, self)._pack()
            if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_ordrsp').id:
            ...


""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['mail'],
    'data': [
        'edi_route_data.xml',
        'edi_route_view.xml',
        'res_partner_view.xml',
        'security/edi_security.xml',
        'security/ir.model.access.csv',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
