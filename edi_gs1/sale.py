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


#TODO: move to another module
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    order_qty = fields.Float(string='Original Order Quantity')

class sale_order(models.Model):
    _inherit = "sale.order"

    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('model','=',self._name),('res_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
   
    def _edi_message_create(self, edi_type):
        self.env['edi.message']._edi_message_create(edi_type=edi_type, obj=self, partner=self.partner_id, check_route=False, check_double=False)

    @api.one
    def action_create_ordrsp(self):
        self._edi_message_create('ORDRSP')

    @api.one
    def action_create_ordrsp_oerk(self):
        self._edi_message_create('ORDRSP-oerk')


    #~ @api.one
    #~ def action_create_invoic(self):
        #~ self._edi_message_create('INVOIC')

    @api.one
    def action_invoice_create(self,grouped=False, states=['confirmed', 'done', 'exception'], date_invoice = False):
        res = super(sale_order,self).action_invoice_create(grouped=grouped, states=states, date_invoice = date_invoice)
        self.env['account.invoice'].browse(res)._edi_message_create('INVOIC')
        return res

    @api.one
    def action_wait(self):
        self.action_create_ordrsp()
        return super(sale_order, self).action_wait()

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    def _edi_message_create(self, edi_type):
        self.env['edi.message']._edi_message_create(edi_type=edi_type, obj=self, partner=self.partner_id, check_route=False, check_double=False)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
