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
    def _picking_ids(self):
        self.picking_ids = [(6, 0, set([l.picking_id.id for l in self.invoice_line]))]
    picking_ids = fields.One2many(string='Stock picking', comodel_name='stock.picking',compute="_picking_ids")
    
class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    picking_id = fields.Many2one(string='Stock picking', comodel_name='stock.picking')

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_invoice_create(self, journal_id, group=False, type='out_invoice'):
        invoices = super(stock_picking, self).action_invoice_create(journal_id, group, type)
        for inv in self.env['account.invoice'].browse(invoices):
             if inv.order_ids and inv.order_ids[0].route_id:
                inv.order_ids[0].route_id.edi_action('stock.picking.action_invoice_create', invoice=inv)
        return invoices

class stock_move(models.Model):
    _inherit = 'stock.move'
        
    @api.model    
    def _create_invoice_line_from_vals(self, move, invoice_line_vals):
        #raise Warning('%s | %s' % (move,invoice_line_vals))
        invoice_line_vals['picking_id'] = move.picking_id.id
        return super(stock_move, self)._create_invoice_line_from_vals(move, invoice_line_vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
