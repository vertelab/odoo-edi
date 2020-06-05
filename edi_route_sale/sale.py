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
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)

class sale_order(models.Model):
    _inherit = 'sale.order'

    route_id = fields.Many2one(comodel_name="edi.route")
    
    @api.one
    def _fix_broken_workflow(self):
        """There is an issue where sale.order creation fails halfway through, causing the workflow to not be created. This function repairs the worflow."""
        if self.env['workflow.instance'].search([('res_type', '=', self._name), ('res_id', '=', self.id)]):
            raise Warning('Workflow already exists! No action taken.')
        wkf_instance = self.env['workflow.instance'].create({
            'res_type': self._name,
            'uid': self.env.user.id,
            'wkf_id': self.env.ref('sale.wkf_sale').id,
            'state': 'active',
            'res_id': self.id,
        })
        wkf_instance = self.env['workflow.workitem'].create({
            'act_id': self.env.ref('sale.act_draft').id,
            'inst_id': wkf_instance.id,
            'subflow_id': None,
            'state': 'complete',
        })
        #Send order response as well.
        self._edi_message_create('edi_gs1.edi_message_type_orderk')
        
    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('model','=',self._name),('res_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")


    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        _logger.warn(vals)
        order =  super(sale_order,self).create(vals)
        if order:
            order.route_id.edi_action('sale.order.create',order=order)
        return order
    
    @api.multi
    def action_cancel(self):
        res =  super(sale_order,self).action_cancel()
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_cancel',order=order,res=res)
        return res
    
    @api.multi
    def action_button_confirm(self):
        res = super(sale_order,self).action_button_confirm()
        _logger.warn("\n\naction_button_confirm begin: %s, %s\n\n" % (res, self.picking_ids))
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_button_confirm',order=order,res=res)
        _logger.warn("\n\naction_button_confirm done!\n\n")
        return res
    
    @api.multi
    def action_wait(self):
        res =  super(sale_order,self).action_wait()
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_wait',order=order,res=res)
        return res
    
    @api.multi
    def action_done(self):
        res =  super(sale_order,self).action_done()
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_done',order=order,res=res)
        return res
    
    @api.multi
    def action_ship_create(self):
        res =  super(sale_order,self).action_ship_create()
        _logger.warn("\n\naction_ship_create %s\n\n" % res)
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_ship_create', order=order, pickings=[p for p in order.picking_ids], res=res)
        _logger.warn("\n\naction_ship_create done\n\n")
        return res
    
    @api.multi
    def action_invoice_create(self, grouped=False, states=None, date_invoice = False):
        #TODO: Check if this works with multiple orders selected
        res =  super(sale_order,self).action_invoice_create(grouped=grouped, states=states, date_invoice = date_invoice)
        invoices = [i for i in self[0].invoice_ids if i.state == 'draft']
        if len(invoices)>0:
            if self.route_id:
                self.route_id.edi_action('sale.order.action_invoice_create', order=self[0], invoice=invoices[-1])
        return res
    
    @api.multi
    def action_invoice_cancel(self):
        res =  super(sale_order,self).action_invoice_cancel()
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_invoice_cancel',order=order,res=res)
        return res
    
    @api.multi
    def action_invoice_end(self):
        res =  super(sale_order,self).action_invoice_end()
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_invoice_end',order=order,res=res)
        return res
    
    @api.multi
    def action_ignore_delivery_exception(self):
        res =  super(sale_order,self).action_ignore_delivery_exception()
        for order in self:
            if order.route_id:
                order.route_id.edi_action('sale.order.action_ignore_delivery_exception',order=order,res=res)
        return res

    def _edi_message_create(self, edi_type, sender=None, recipient=None, check_double=False,):
        self.env['edi.message']._edi_message_create(edi_type=edi_type, obj=self, consignee=self.partner_id, route=self.route_id, sender=sender, recipient=recipient, check_double=check_double)

class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('invoice_id', 'invoice_id.order_ids')
    @api.multi
    def _order_ids(self):
        for record in self:
            if record.invoice_id:
                record.order_ids = record.invoice_id.order_ids
            else:
                #TODO: Breaks on create if field is shown in the view. Check record.id?
                record.order_ids = self.env['sale.order'].search([('invoice_ids', '=', record.id)])
    order_ids = fields.Many2many(string='Orders', comodel_name='sale.order', compute="_order_ids")
    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Credited Invoice')
    
    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        values = super(account_invoice, self)._prepare_refund(invoice, date, period_id, description, journal_id)
        values.update({
            'invoice_id': invoice.id,
            'picking_ids': [(6, 0, [o.id for o in invoice.picking_ids])],
        })
        _logger.warn(values)
        return values
    
    def _get_route(self):
        if self.order_ids and self.order_ids[0].route_id:
            return self.order_ids[0].route_id
        return None

    @api.one
    def _edi_message_create(self, edi_type, check_double=False):
        orders = self.order_ids
        self.env['edi.message']._edi_message_create(
            edi_type=edi_type,
            obj=self,
            sender=orders and orders[0].unb_recipient or None,
            recipient=orders and orders[0].unb_sender or None,
            consignee=orders and orders[0].nad_by or self.partner_id,
            route=orders and orders[0].route_id,
            check_double=check_double)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        invoice =  super(account_invoice, self).create(vals)
        if invoice and invoice._get_route():
            _logger.info("create Caller ID: %s; (account) %s %s" % ('account.invoice.create', invoice, invoice._get_route()))
            invoice._get_route().edi_action('account.invoice.create', invoice=invoice)
        return invoice

    @api.multi
    def action_cancel(self):
        res =  super(account_invoice, self).action_cancel()
        for invoice in self:
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_cancel', invoice=invoice, res=res)
        return res

    @api.multi
    def action_move_create(self):
        res =  super(account_invoice, self).action_move_create()
        for invoice in self:
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_move_create', invoice=invoice,res=res)
        return res

    @api.multi
    def action_draft(self):
        res =  super(account_invoice, self).action_draft()
        for invoice in self:
            _logger.info("action_draft Caller ID: %s; (account) %s %s" % ('account.invoice.action_draft', invoice, invoice._get_route()))
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_draft', invoice=invoice, res=res)
        return res

    @api.multi
    def action_create(self):
        res =  super(account_invoice, self).action_create()
        for invoice in self:
            _logger.info("action_create Caller ID: %s; (account) %s %s" % ('account.invoice.action_create', invoice, invoice._get_route()))
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_create', invoice=invoice, res=res)
        return res

    @api.multi
    def invoice_validate(self):
        res =  super(account_invoice, self).invoice_validate()
        for invoice in self:
            _logger.info("invoice_validate Caller ID: %s; (account) %s %s" % ('account.invoice.invoice_validate', invoice, invoice._get_route()))
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.invoice_validate', invoice=invoice)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
