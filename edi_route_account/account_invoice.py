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

    
class account_invoice(models.Model):
    _inherit = "account.invoice"

#    picking_ids = fields.Many2many(string='Stock picking', comodel_name='stock.picking')
#    order_id = fields.Many2one(string='Sale order', comodel_name='sale.order')

    def _get_route(self): 
        orders = self.env['sale.order'].search([('invoice_ids','in',self.id)])
        if len(orders)>0:
            return orders[0].route_id
        return None

    @api.one
    def _edi_message_create(self,edi_type,check_double=False):
        orders = self.env['sale.order'].search([('invoice_ids','in',self.id)])
        self.env['edi.message']._edi_message_create(edi_type=edi_type,obj=self,partner=self.partner_id,route=orders and orders[0].route_id,check_double=check_double)
        
    @api.model
    def create(self, vals):
        invoice =  super(account_invoice,self).create(vals)
        if invoice and invoice._get_route():
            invoice._get_route().edi_action('account.invoice.create',order=order)
        return invoice
    @api.multi
    def action_cancel(self):
        res =  super(account_invoice,self).action_cancel()
        for invoice in self:
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_cancel',invoice=invoice,res=res)
        return res
    @api.multi
    def action_draft(self):
        res =  super(account_invoice,self).action_draft()
        for invoice in self:
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_draft',invoice=invoice,res=res)
        return res
    @api.multi
    def action_create(self):
        res =  super(account_invoice,self).action_create()
        for invoice in self:
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_create',invoice=invoice,res=res)
        return res


#~ class sale_order(models.Model):
    #~ _inherit = 'sale.order'

    #~ @api.model
    #~ def _make_invoice(self, order, lines):
        #~ inv_id = super(sale_order, self)._make_invoice(order, lines)
        #~ self.env['account.invoice'].browse(inv_id).write({'order_id' : order.id})
        #~ return inv_id

#~ class stock_picking(models.Model):
    #~ _inherit = 'stock.picking'
    
    #~ @api.multi
    #~ def action_invoice_create(self,journal_id, group=False, type='out_invoice'):
        #~ invoices = super(stock_picking, self).action_invoice_create(journal_id, group=group,type=type)
        #~ if len(invoices) > 0:
            #~ self.env['account.invoice'].browse(invoices[0]).write({
                #~ 'picking_ids' : [(6, 0, [p.id for p in self])],
                #~ 'order_id': [p.sale_id.id for p in self][0],
            #~ })
        #~ return invoices

    
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
