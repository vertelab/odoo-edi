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
from openerp.tools import float_compare

import logging
_logger = logging.getLogger(__name__)


#TODO: move to another module
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    order_qty = fields.Float(string='Original Order Quantity')
    is_available = fields.Selection([('true', 'true'), ('false', 'false')], compute='_is_available')

    @api.one
    def _is_available(self):
        self.is_available = 'true'
        if not self._check_routing(self.product_id, self.order_id.warehouse_id.id):
            compare_qty = float_compare(self.product_id.virtual_available, self.product_uom_qty, precision_rounding=self.product_id.uom_id and self.product_id.uom_id.rounding or 0.01)
            if compare_qty == -1:
                self.is_available = 'false'


class sale_order(models.Model):
    _inherit = "sale.order"

    nad_by = fields.Many2one(comodel_name='res.partner',help="Byer, party to whom merchandise and/or service is sold.")
    nad_su = fields.Many2one(comodel_name='res.partner',help="Supplier, party who supplies goods and/or services.")
    nad_sn = fields.Many2one(comodel_name='res.partner',help="Store keeper,A party keeping a shop or store.")
    nad_cn = fields.Many2one(comodel_name='res.partner',help="Consignee, party to which goods are consigned.")
    nad_dp = fields.Many2one(comodel_name='res.partner',help="Delivery party, party to which goods should be delivered, if not identical with consignee.")
    unb_sender = fields.Many2one(comodel_name='res.partner')
    unb_recipient = fields.Many2one(comodel_name='res.partner')
    dtm_delivery = fields.Date('Delivery Date', help='Date from DTM with code 2.')

    #~ def _edi_message_create(self, edi_type):
        #~ self.env['edi.message']._edi_message_create(edi_type=edi_type, obj=self, partner=self.partner_id, check_route=False, check_double=False)
#~
    #~ @api.one
    #~ def action_create_ordrsp(self):
        #~ if self.route_id:
            #~ self.route_id.edi_action('sale.order.action_create_ordrsp', order=self)
#~
    #~ @api.one
    #~ def action_create_ordrsp_oerk(self):
        #~ if self.route_id:
            #~ route_id.edi_action('sale.order.action_create_ordrsp_oerk', order=self)
#~
    #~ @api.multi
    #~ def action_invoice_create(self, grouped=False, states=['confirmed', 'done', 'exception'], date_invoice = False):
        #~ res = super(sale_order, self).action_invoice_create(grouped=grouped, states=states, date_invoice = date_invoice)
        #~ _logger.warn('res: %s' % res)
        #~ self.env['account.invoice'].browse(res)._edi_message_create('INVOIC')
        #~ return res

    #~ @api.multi
    #~ def action_wait(self):
        #~ for order in self:
            #~ order.action_create_ordrsp()
        #~ return super(sale_order, self).action_wait()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
