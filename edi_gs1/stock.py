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


#~ class stock_production_lot(models.Model):
    #~ _inherit = 'stock.production.lot'

    #~ sscc = fields.Char(String="SSCC#", help="SSCC-number on the pallet")    
class stock_quant_package(models.Model):
    _inherit = 'stock.quant.package'

    sscc = fields.Char(String="SSCC#", help="SSCC-number on the pallet")    

class stock_move(models.Model):
    _inherit = 'stock.move'
    
    qty_difference_reason = fields.Selection(string = 'Qty Difference Reason', selection = [
        ('AS', 'Artikeln har utgått ur sortimentet'),
        ('AUE', 'Okänt artikelnummer'),
        ('AV', 'Artikeln slut i lager'),
        ('PC', 'Annan förpackningsstorlek'),
        ('X35', 'Artikeln har dragits tillbaka'),
        ('Z1', 'Slut för säsongen'),
        ('Z2', 'Tillfälligt spärrad för försäljning (varan finns men kan ha karensdagar)'),
        ('Z3', 'Nyhet, ej i lager'),
        ('Z4', 'Tillfälligt spärrad på grund av konflikt'),
        ('Z5', 'Restnoterad artikel från tillverkare och måste beställas på nytt'),
        ('Z6', 'Produktionsproblem'),
        ('Z7', 'Slut i lager hos tillverkaren'),
        ('Z8', 'Beställningsvara'),
        ('Z9', 'Restnoterad från tillverkaren'),
        ('ZZ', 'Annan orsak'),
    ])
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
