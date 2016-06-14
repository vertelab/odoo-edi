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
    
    @api.model
    def _invoice_create_line(self, moves, journal_id, inv_type='out_invoice'):
        #Overridden to add picking_ids attribute to invoices
        invoice_obj = self.env['account.invoice']
        move_obj = self.env['stock.move']
        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(moves, inv_type)
        product_price_unit = {}
        picking_ids = []
        for move in moves:
            if not move.picking_id.id in picking_ids:
                picking_ids.append(move.picking_id.id)
        for move in moves:
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(move, company)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(key, inv_type, journal_id, move)
            
            if key not in invoices:
                # Get account and payment terms
                
                #Add picking_ids
                invoice_vals['picking_ids'] = [(6, 0, picking_ids)]
                invoice_id = self._create_invoice_from_picking(move.picking_id, invoice_vals)
                invoices[key] = invoice_id
            else:
                invoice = invoice_obj.browse(invoices[key])
                merge_vals = {}
                if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
                    invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
                    merge_vals['origin'] = ', '.join(invoice_origin)
                if invoice_vals.get('name', False) and (not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
                    invoice_name = filter(None, [invoice.name, invoice_vals['name']])
                    merge_vals['name'] = ', '.join(invoice_name)
                if merge_vals:
                    invoice.write(merge_vals)
            context = dict(self.env.context, fp_id=invoice_vals.get('fiscal_position', False))
            invoice_line_vals = move_obj.with_context(context)._get_invoice_line_vals(move, partner, inv_type)
            invoice_line_vals['invoice_id'] = invoices[key]
            invoice_line_vals['origin'] = origin
            if not is_extra_move[move.id]:
                product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
            if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
                invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
            if is_extra_move[move.id]:
                desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
                    (inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
                invoice_line_vals['name'] += ' ' + desc if desc else ''
                if extra_move_tax[move.picking_id, move.product_id]:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
                #the default product taxes
                elif (0, move.product_id) in extra_move_tax:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]

            move_obj._create_invoice_line_from_vals(move, invoice_line_vals)
            move.write({'invoice_state': 'invoiced'})
        
        invoice_obj = invoice_obj.browse(invoices.values())
        invoice_obj.button_compute(set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
