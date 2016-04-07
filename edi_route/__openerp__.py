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
Other modules will extend these classes with communication protocolls, edi-message formats
and mapping to Odoo-classes.

 +---------------------------+---------------------------------+
 | edi.route                 | Recieves and sends envelopes    |
 |                           | using a communication protocoll |
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

edi.route uses automation (ir.cron) to empty the mailbox when 
recieving envelopes (edi-messages). Outgoing transfer initiates
when edi.route finds ready edi.envelopes for its route. Every 
run identifies with an internal sequence number. 

edi.envelope also uses automation to find messages for the 
same route to be folded in an envelope and passed to the 
route. Every envelope identifies with an internal sequence number. 

Each edi.message identifies with an internal sequence number. Edi-type
and Consignee are keys to find a proper route for outgoing messages.

Res.partner

""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['edi','mail'],
    'data': [ 'edi_route_view.xml','res_partner_view.xml','edi_route_data.xml'
    #'security/ir.model.access.csv',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
