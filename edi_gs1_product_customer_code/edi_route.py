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

class edi_message(models.Model):
    _inherit = 'edi.message'
    
    def _get_customer_product_code(self, product, customer):
        code = self.env['product.customer.code'].search([('product_id', '=', product.id)('partner_id', '=', customer.id)])
        if code:
            return code.product_code
        return super(edi_message, self)._get_customer_product_code(product, customer)
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
