
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2004-2009 vertel.se
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import wizard
import pooler
import os
import json
import datetime
from osv import fields, osv
from tools.translate import _

class ica_mrpjournal_do_import_order_sale(wizard.interface):
    def _do_create_saleorder(self, cr, uid, data, context):
        print data, context
        today = datetime.datetime.today()
        print today
        order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        partner_cr =  pooler.get_pool(cr.dbname).get('res.partner')
        address_cr =  pooler.get_pool(cr.dbname).get('res.partner.address')
        product_cr =  pooler.get_pool(cr.dbname).get('product.product')
        sale_order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        line_cr = pooler.get_pool(cr.dbname).get('sale.order.line')
        tax_cr = pooler.get_pool(cr.dbname).get('sale.order.tax')

        #order = pooler.get_pool(cr.dbname).get('sale.order').create(cr, uid, {'partner_id': 1, 'state': 'done',})
        #line = pooler.get_pool(cr.dbname).get('sale.order.line').create(cr, uid, {'product_id': 1, 'product_uom_qty': 1,})
        #tax = pooler.get_pool(cr.dbname).get('sale.order.tax').create(cr, uid, {'order_line_id': line, 'tax_id': 1})
        return {}

    states = {
            'init' : {
                'actions' : [_do_create_saleorder],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_import_order_sale("ica.do_import_order_sale")

