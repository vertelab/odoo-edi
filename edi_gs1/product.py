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
    

class product_packaging(models.Model):
    _inherit = "product.packaging"

    ean = fields.Char(string="GTIN-14", size=14, help="The EAN/GTIN14 number of the package unit.")
    gtin14 = fields.Char(string="GTIN-14", size=14, help="The EAN/GTIN14 number of the package unit.")
    
    def _check_gtin14_key(self, cr, uid, ids, context=None):
        for pack in self.browse(cr, uid, ids, context=context):
            if not check_gtin14(pack.ean):
                return False
        return True
    _constraints = [(_check_gtin14_key, 'Error: Invalid gtin-14 code', ['gtin14'])]
        
def gtin14_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if the string has the wrong length"""
    if len(eancode) != 14:
        return -1
    return int(eancode[-1])
    
    oddsum=0
    evensum=0
    total=0
    eanvalue=eancode
    reversevalue = eanvalue[::-1]
    finalean=reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total=(oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10
    return check

def check_gtin14(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 14:
        return False
    try:
        int(eancode)
    except:
        return False
    return gtin14_checksum(eancode) == int(eancode[-1])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
