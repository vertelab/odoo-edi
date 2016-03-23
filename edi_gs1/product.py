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

class product_product(models.Model):
    _inherit='product.product'
    
    gs1_gtin14 = fields.Char(string="GTIN-14",help="GS1 Global Trade Item Number (GTIN) for outer packages or pallets")
    gs1_gtin13 = fields.Char(string="GTIN-13",help="GS1 Global Trade Item Number (GTIN) for consumer products")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
