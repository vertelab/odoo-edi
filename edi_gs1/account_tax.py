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

class account_tax(models.Model):
    _inherit = 'account.tax' 
    
    gs1_tax_type = fields.Selection(selection = [
        ('AAE', 'Energy Tax'),
        ('ENV', 'Environment Tax'),
        ('VAT', 'Value Added Tax')
    ])
    gs1_tax_category = fields.Selection(selection = [
        ('B', 'Limited right for deduction'),
        ('E', 'Excluded from VAT'),
        ('H', 'Hotel, camping, etc.'),
        ('L', 'Public service'),
        ('M', 'Food'),
        ('R', 'Restaurant services'),
        ('S', 'Standard'),
        ('T', 'Papers, books etc'),
        ('U', 'Travels'),
        ('Z', 'Zero % tax'),
    ])
