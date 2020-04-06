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

class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('model','=',self._name),('res_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
   
    @api.one
    def _edi_message_create(self, edi_type, check_double=False):
        if self.sale_id:
            self.env['edi.message']._edi_message_create(
                edi_type = edi_type,
                obj = self,
                sender = self.sale_id.unb_recipient,
                recipient = self.sale_id.unb_sender,
                consignee = self.sale_id.partner_id,
                route = self.sale_id.route_id,
                check_double = check_double
            )
    
    #~ def _get_route(self):
        #~ #raise Warning(self.group_id)
        #~ #routes = [o.route_id for o in self.env['sale.order'].search([('procurement_group_id', '=', self.group_id.id)])]
        #~ route = [p.sale_id.route_id for p in self.picking_ids ]
        #~ return routes and routes[0] or None
        
    @api.model
    def create(self, vals):
        picking =  super(stock_picking,self).create(vals)
        if picking and picking.sale_id and picking.sale_id.route_id:
            picking.sale_id.route_id.edi_action('stock.picking.create', picking=picking)
        return picking
    
    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        res =  super(stock_picking, self).do_transfer(cr, uid, picking_ids, context)
        if res and picking_ids:
            for picking in self.browse(cr, uid, picking_ids, context):
                if picking.sale_id and picking.sale_id.route_id:
                    picking.sale_id.route_id.edi_action('stock.picking.do_transfer', picking=picking)
        return res
    
    @api.multi
    def action_cancel(self):
        res =  super(stock_picking,self).action_cancel()
        for picking in self:
            if picking.sale_id and picking.sale_id.route_id:
                picking.sale_id.route_id.edi_action('stock.picking.action_cancel', picking=picking,res=res)
        return res
    @api.multi
    def action_confirm(self):
        res =  super(stock_picking,self).action_confirm()
        for picking in self:
            if picking.sale_id and picking.sale_id.route_id:
                picking.sale_id.route_id.edi_action('stock.picking.action_confirm',picking=picking,res=res)
        return res
    @api.multi
    def action_assign(self):
        res =  super(stock_picking,self).action_assign()
        for picking in self:
            if picking.sale_id and picking.sale_id.route_id:
                picking.sale_id.route_id.edi_action('stock.picking.action_assign',picking=picking,res=res)
        return res
    @api.multi
    def action_done(self):
        res =  super(stock_picking,self).action_done()
        for picking in self:
            if picking.sale_id and picking.sale_id.route_id:
                picking.sale_id.route_id.edi_action('stock.picking.action_done',picking=picking,res=res)
        return res
    @api.multi
    def action_pack(self):
        res =  super(stock_picking,self).action_pack()
        for picking in self:
            if picking.sale_id and picking.sale_id.route_id:
                picking.sale_id.route_id.edi_action('stock.picking.action_pack',picking=picking,res=res)
        return res


class stock_move(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        move =  super(stock_move,self).create(vals)
        if move and move.picking_id.sale_id and move.picking_id.sale_id.route_id:
            move.picking_id.sale_id.route_id.edi_action('stock.move.create',move=move)
        return move
    @api.multi
    def action_cancel(self):
        res =  super(stock_move,self).action_cancel()
        for move in self:
            if move.picking_id.sale_id and move.picking_id.sale_id.route_id:
                move.picking_id.sale_id.route_id.edi_action('stock.move.action_cancel',move=move,res=res)
        return res
    @api.multi
    def action_confirm(self):
        res =  super(stock_move,self).action_confirm()
        for move in self:
            if move.picking_id.sale_id and move.picking_id.sale_id.route_id:
                move.picking_id.sale_id.route_id.edi_action('stock.move.action_confirm',move=move,res=res)
        return res
    @api.multi
    def action_done(self):
        res =  super(stock_move,self).action_done()
        for move in self:
            if move.picking_id.sale_id and move.picking_id.sale_id.route_id:
                move.picking_id.sale_id.route_id.edi_action('stock.move.action_done',move=move,res=res)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
