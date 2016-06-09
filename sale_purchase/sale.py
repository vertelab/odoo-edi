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

import logging
_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.one
    def _get_purchase_orders(self):
        self.purchase_ids = [(6,0,[p.id for p in set(self.env['purchase.order.line'].search([('order_id','=',self.id)]))])]
    purchase_ids = fields.Many2many(comodel_name="purchase.order",compute='_get_purchase_orders')
    
    
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
        for so in self.browse(cr, uid, ids, context=context):
            purchase_ids += [p.id for p in so.purchase_ids]
            
        #choose the view_mode accordingly
        if len(self.purchase_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, purchase_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'purchase', 'view_purchase_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = purchase_ids and purchase_ids[0] or False
        return result
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
