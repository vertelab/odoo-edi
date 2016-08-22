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

    def _get_route(self):
        _logger.info("_get route account %s" % self)
        orders = self.env['sale.order'].search([('invoice_ids', 'in', self.id)])
        _logger.info("---------------- %s" % orders)
        _logger.info("**************** %s" % orders[0].route_id)
        if len(orders)>0:
            return orders[0].route_id
        return None

    def _get_order(self):
        _logger.info("_get order account %s" % self)
        orders = self.env['sale.order'].search([('invoice_ids', 'in', self.id)])
        if len(orders)>0:
            return orders[0]
        return None

    @api.one
    def _edi_message_create(self, edi_type, check_double=False):
        orders = self.env['sale.order'].search([('invoice_ids', 'in', self.id)])
        self.env['edi.message']._edi_message_create(
            edi_type=edi_type,
            obj=self,
            sender=orders and orders[0].unb_recipient or None,
            recipient=orders and orders[0].unb_sender or None,
            consignee=orders and orders[0].nad_by or self.partner_id,
            route=orders and orders[0].route_id,
            check_double=check_double)

    @api.model
    def create(self, vals):
        invoice =  super(account_invoice, self).create(vals)
        if invoice and invoice._get_route():
            _logger.info("Caller ID: %s; (account) %s %s" % ('account.invoice.create', invoice, invoice._get_route()))
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
            _logger.info("Caller ID: %s; (account) %s %s" % ('account.invoice.action_draft', invoice, invoice._get_route()))
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_draft', invoice=invoice, res=res)
        return res

    @api.multi
    def action_create(self):
        res =  super(account_invoice, self).action_create()
        for invoice in self:
            _logger.info("Caller ID: %s; (account) %s %s" % ('account.invoice.action_create', invoice, invoice._get_route()))
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.action_create', invoice=invoice, res=res)
        return res

    @api.multi
    def invoice_validate(self):
        res =  super(account_invoice, self).invoice_validate()
        for invoice in self:
            _logger.info("Caller ID: %s; (account) %s %s" % ('account.invoice.invoice_validate', invoice, invoice._get_route()))
            if invoice._get_route():
                invoice._get_route().edi_action('account.invoice.invoice_validate', invoice=invoice)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
