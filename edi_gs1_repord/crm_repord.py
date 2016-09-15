# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _
from openerp import http
from openerp.http import request
import datetime
import logging
import base64
_logger = logging.getLogger(__name__)

import openerp.addons.decimal_precision as dp

class rep_order(models.Model):
    _inherit = "rep.order"
    
    nad_by = fields.Many2one(comodel_name='res.partner',help="Byer, party to whom merchandise and/or service is sold.")
    nad_su = fields.Many2one(comodel_name='res.partner',help="Supplier, party who supplies goods and/or services.")
    nad_sn = fields.Many2one(comodel_name='res.partner',help="Store keeper,A party keeping a shop or store.")
    nad_cn = fields.Many2one(comodel_name='res.partner',help="Consignee, party to which goods are consigned.")
    nad_dp = fields.Many2one(comodel_name='res.partner',help="Delivery party, party to which goods should be delivered, if not identical with consignee.")
    nad_ito = fields.Many2one(comodel_name='res.partner',help="Invoice party, party to which bill should be invoiced, if not identical with consignee.")
    unb_sender = fields.Many2one(comodel_name='res.partner')
    unb_recipient = fields.Many2one(comodel_name='res.partner')
    dtm_delivery = fields.Date('Delivery Date', help='Date from DTM with code 2.')
    dtm_issue = fields.Date('Issued Date', help='Date from DTM with code 137.')
    
    @api.one
    def action_convert_to_sale_order(self):
        super(rep_order, self).action_convert_to_sale_order()
        if self.order_type == 'order':
            self.write({
                'route_id': self.env.ref('edi_gs1.route_esap20').id,
                'nad_by': self.partner_id.id,
                'nad_su': self.env.ref('base.main_partner').id,
                'unb_sender': self.env.ref('base.main_partner').id,
                'unb_recipient': self.partner_id.parent_id.id,
            })
            self.route_id.edi_action('rep.order.action_convert_to_sale_order', order=self)
        elif self.order_type == '3rd_party':
            self.write({
                'route_id': self.env.ref('edi_gs1.route_esap20').id,
                'nad_by': self.partner_id.id,
                'nad_su': self.env.ref('base.main_partner').id,
                'unb_sender': self.env.ref('base.main_partner').id,
                'unb_recipient': self.partner_id.parent_id.id,
            })
            self.route_id.edi_action('rep.order.action_convert_to_sale_order', order=self)
    
    @api.one
    def _edi_message_create(self, edi_type, sender=None, recipient=None, check_double=False,):
        if not sender:
            sender = self.unb_sender
        if not recipient:
            recipient = self.unb_recipient
        _logger.warn('creating message')
        self.env['edi.message']._edi_message_create(edi_type=edi_type, obj=self, consignee=self.partner_id.parent_id, route=self.route_id, sender=sender, recipient=recipient, check_double=check_double)


