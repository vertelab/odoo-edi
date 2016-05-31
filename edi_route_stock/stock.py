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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('model','=',self._name),('res_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
   
    @api.one
    def _edi_message_create(self,edi_type):
        orders = self.env['sale.order'].search([('picking_ids','in',self.id)])
        self.env['edi.message']._edi_message_create(edi_type=edi_type,obj=self,partner=self.partner_id,route=orders and orders[0].route_id,check_double=False)

    def _get_route(self):
        return [o.route_id for o in self.env['sale.order'].search([('picking_ids','in',self.id)])][0]

    @api.model
    def create(self, vals):
        picking =  super(stock_picking,self).create(vals)
        if picking and picking._get_route():
            picking._get_route().edi_action('stock.picking.caller_create',picking=picking)
        return picking
    @api.multi
    def action_cancel(self):
        res =  super(stock_picking,self).action_cancel()
        for picking in self:
            if picking._get_route():
                picking._get_route().edi_action('stock.picking.caller_action_cancel',picking=picking,res=res)
        return res
    @api.multi
    def action_confirm(self):
        res =  super(stock_picking,self).action_confirm()
        for picking in self:
            if picking._get_route():
                picking._get_route().edi_action('stock.picking.caller_action_confirm',picking=picking,res=res)
        return res
    @api.multi
    def action_assign(self):
        res =  super(stock_picking,self).action_assign()
        for picking in self:
            if picking._get_route():
                picking._get_route().edi_action('stock.picking.caller_action_assign',picking=picking,res=res)
        return res
    @api.multi
    def action_done(self):
        res =  super(stock_picking,self).action_done()
        for picking in self:
            if picking._get_route():
                picking._get_route().edi_action('stock.picking.caller_action_done',picking=picking,res=res)
        return res
    @api.multi
    def action_pack(self):
        res =  super(stock_picking,self).action_pack()
        for picking in self:
            if picking._get_route():
                picking._get_route().edi_action('stock.picking.caller_action_pack',picking=picking,res=res)
        return res


class stock_move(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        move =  super(stock_move,self).create(vals)
        if move and move.picking_id._get_route():
            move.picking_id._get_route().edi_action('stock.move.caller_move_create',move=move)
        return move
    @api.multi
    def action_cancel(self):
        res =  super(stock_move,self).action_cancel()
        for move in self:
            if move.picking_id._get_route():
                move.picking_id._get_route().edi_action('stock.move.caller_move_action_cancel',move=move,res=res)
        return res
    @api.multi
    def action_confirm(self):
        res =  super(stock_move,self).action_confirm()
        for move in self:
            if move.picking_id._get_route():
                move.picking_id._get_route().edi_action('stock.move.caller_move_action_confirm',move=move,res=res)
        return res
    @api.multi
    def action_done(self):
        res =  super(stock_move,self).action_done()
        for move in self:
            if move.picking_id._get_route():
                move.picking_id._get_route().edi_action('stock.move.caller_move_action_done',move=move,res=res)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
