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
    
    @api.one
    def _edi_message_create(self,edi_type):
        orders = self.env['sale.order'].search([('invoice_ids','in',self.id)])
        self.env['edi.message']._edi_message_create(edi_type=edi_type,obj=self,partner=self.partner_id,route=orders and orders[0].route_id,check_double=False)


    @api.model
    def create(self, vals):
        invoice =  super(account_invoice,self).create(vals)
        if invoice and invoice.order_id and invoice.order_id.route_id:
            invoice.order_id.route_id.edi_action('account_invoice.caller_create',order=order)
        return invoice
    @api.multi
    def action_cancel(self):
        res =  super(account_invoice,self).action_cancel()
        for invoice in self:
            if invoice.order_id and invoice.order_id.route_id:
                invoice.order_id.route_id.edi_action('account_invoice.caller_action_cancel',invoice=invoice,res=res)
        return res
    @api.multi
    def action_draft(self):
        res =  super(account_invoice,self).action_draft()
        for invoice in self:
            if invoice.order_id and invoice.order_id.route_id:
                invoice.order_id.route_id.edi_action('account_invoice.caller_action_draft',invoice=invoice,res=res)
        return res
    @api.multi
    def action_create(self):
        res =  super(account_invoice,self).action_create()
        for invoice in self:
            if invoice.order_id and invoice.order_id.route_id:
                invoice.order_id.route_id.edi_action('account_invoice.caller_action_create',invoice=invoice,res=res)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
