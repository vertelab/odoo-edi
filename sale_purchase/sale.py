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
from odoo.tools.float_utils import float_compare


import logging
_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.one
    def _get_purchase_orders(self):
        po = self.env['purchase.order']
        for l in self.order_line:
            for procurement in l.procurement_ids:
                po = po | procurement.purchase_id
        if po:
            self.purchase_ids = po
        else:
            self.purchase_ids = None
    purchase_ids = fields.Many2many(comodel_name="purchase.order", compute='_get_purchase_orders')

    @api.depends('purchase_ids')
    @api.one
    def _purchase_count(self):
        #raise Warning(self.purchase_ids,len(self.purchase_ids))
        if self.purchase_ids:
            self.purchase_count = len(self.purchase_ids)
        else:
            self.purchase_count = 0
    purchase_count = fields.Integer(compute='_purchase_count', string="# purchases")

    def action_view_purchase(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing purchase orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'purchase', 'purchase_form_action')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]

        #compute the number of purchase orders to display
        purchase_ids = []
        pos = self.browse(cr, uid, ids, context=context)
        for po in pos:
            purchase_ids += [p.id for p in po.purchase_ids]

        #choose the view_mode accordingly
        if len(pos) > 0 and len(purchase_ids) != 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, purchase_ids)) + "])]"
        elif len(pos) > 0:
            res = mod_obj.get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = purchase_ids and purchase_ids[0] or False
        return result

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    is_available = fields.Selection([('true', 'true'), ('false', 'false')], compute='_is_available')

    @api.one
    def _is_available(self):
        self.is_available = 'true'
        if self.order_id.state not in ['draft', 'sent']:
            return
        elif not self._check_routing(self.product_id, self.order_id.warehouse_id.id):
            if float_compare(self.product_id.virtual_available, self.product_uom_qty, precision_rounding=self.product_id.uom_id and self.product_id.uom_id.rounding or 0.01) == -1:
                self.is_available = 'false'
        elif self.order_id.purchase_ids:
            pline = None
            for p in self.order_id.purchase_ids:
                for l in p.order_line:
                    if l.product_id.id == self.product_id.id:
                        pline = l
            if pline and float_compare(pline.product_qty, self.product_uom_qty, precision_rounding=self.product_id.uom_id and self.product_id.uom_id.rounding or 0.01) == -1:
                self.is_available = 'false'

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def _partner_to_invoice(self):
        self.partner_to_invoice = self._get_partner_to_invoice(self) or None
    partner_to_invoice = fields.Many2one(comodel_name='res.partner',compute='_partner_to_invoice')
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
