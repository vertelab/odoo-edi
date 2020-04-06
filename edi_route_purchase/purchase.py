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
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

class purchase_order(models.Model):
    _inherit = "purchase.order"
    
    purchase_route_id = fields.Many2one(comodel_name="edi.route")
    
    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('model','=',self._name),('res_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
   
    @api.one
    def _edi_message_create(self,edi_type,check_double=False):
        orders = self.env['sale.order'].search([('purchase_ids','in',self.id)])
        if orders and orders[0]:
            self.env['edi.message']._edi_message_create(
                edi_type=edi_type,
                obj=self,
                sender=orders[0].unb_recipient,
                recipient=orders[0].unb_sender,
                consignee=self.partner_id,route=orders and orders[0].route_id,
                check_double=check_double)


    def _get_route(self):
        routes = []
        for procurement in self.env['procurement.order'].search([('purchase_id', '=', self.id)]):
            routes += [o.route_id for o in self.env['sale.order'].search([('procurement_group_id', '=', procurement.group_id.id)])]
        if self.purchase_route_id:
            routes += [self.purchase_route_id]
        return routes and list(set(routes)) or []

    @api.model
    def create(self, vals):
        if vals.get('date_order') and vals.get('date_order') < fields.Date.today():
            vals['date_order'] = fields.Date.today()
        purchase = super(purchase_order,self).create(vals)
        if not purchase.purchase_route_id:
            if purchase.partner_id.purchase_route_id:
                purchase.purchase_route_id = purchase.partner_id.purchase_route_id.id
            elif purchase.partner_id.parent_id and purchase.partner_id.parent_id.purchase_route_id:
                purchase.purchase_route_id = purchase.partner_id.parent_id.purchase_route_id.id
        for r in purchase._get_route():
            r.edi_action('purchase.order.create',purchase=purchase)
        return purchase    
    @api.multi
    def wkf_bid_received(self):
        res =  super(purchase_order,self).wkf_bid_received()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.wkf_bid_received',purchase=purchase,res=res)
        return res
    @api.multi
    def wkf_confirm_order(self):
        res =  super(purchase_order,self).wkf_confirm_order()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.wkf_confirm_order',purchase=purchase,res=res)
        return res
    @api.multi
    def wkf_action_cancel(self):
        res =  super(purchase_order,self).wkf_action_cancel()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.wkf_action_cancel',purchase=purchase,res=res)
        return res
    @api.multi
    def wkf_approve_order(self):
        res =  super(purchase_order,self).wkf_approve_order()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.wkf_approve_order',purchase=purchase,res=res)
        return res
    @api.multi
    def action_invoice_create(self):
        res =  super(purchase_order,self).action_invoice_create()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.action_invoice_create',purchase=purchase,res=res)
        return res
    @api.multi
    def invoice_done(self):
        res =  super(purchase_order,self).invoice_done()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.invoice_done',purchase=purchase,res=res)
        return res
    @api.multi
    def action_picking_create(self):
        res =  super(purchase_order,self).action_picking_create()
        for purchase in self:
            for r in purchase._get_route():
                r.edi_action('purchase.order.action_picking_create',purchase=purchase,res=res)
        return res

class res_partner(models.Model):
    _inherit='res.partner'

    purchase_route_id = fields.Many2one(comodel_name="edi.route",string="Default Purchase Route",help="Supplier uses this route for Purchase Orders")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
