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

    picking_ids = fields.Many2many(string='Stock picking', comodel_name='stock.picking')

    def _get_route(self):
        _logger.info("_get route srtock %s" % self)

        route = super(account_invoice, self)._get_route()
        if not route:
            route = [p.sale_id.route_id for p in self.picking_ids]
            _logger.info("_get route srtock route %s %s" % (route,self.picking_ids))
            return route and route[0] or None
        return route

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    @api.multi
    def action_invoice_create(self,journal_id, group=False, type='out_invoice'):
        invoices = super(stock_picking, self).action_invoice_create(journal_id, group=group,type=type)
        if len(invoices) > 0:
            self.env['account.invoice'].browse(invoices[0]).write({
                'picking_ids' : [(6, 0, [p.id for p in self])],
#                'order_id': [p.sale_id.id for p in self][0],
            })
        return invoices

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        result = super(stock_picking, self)._get_invoice_vals(key, inv_type, journal_id, move)
        result['picking_ids'] = [(6, 0,[move.picking_id.id])]
#        result['order_id'] = move.picking_id.sale_id.id
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
