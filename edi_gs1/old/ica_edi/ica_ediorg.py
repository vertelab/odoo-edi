# -*- encoding: utf-8 -*-
##############################################################################
#
#    Azzar.se  anders.wallenquist@vertel.se
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

from osv import osv
from osv import fields
import datetime

# http://docs.google.com/Doc?docid=0AQtT8KjrXSkgZGNjbXFwcjlfNTc4Z3A4c3doZHc&hl=en

class ica_edi(osv.osv):
    _name = "ica.edi" 
    _description = "ICA EDI"
    _columns = {
        'next_invoicenbr': fields.integer("Next Invoicenbr"),
        'next_sscc': fields.integer("Next SSCC"),
        'next_desadv': fields.integer("Next DESADV/DSPADV"),
    }
ica_edi()

class ica_edi_sscc(osv.osv):
    _name = "ica.sscc" 
    _description = "ICA SSCC"
    _columns = {
        'sscc': fields.char("SSCC",size=18),
        'line_id': fields.integer('Orderline'),
        'EANSENDER': fields.char('EANSENDER', size=25),
        'EANRECEIVER': fields.char('EANRECEIVER', size=25),
        'EANSHOP': fields.char('EANSHOP', size=25),
        'CUSTOMERNUMBER': fields.char('CUSTOMERNUMBER', size=25),
        'DELDATESHOP': fields.char('DELDATESHOP', size=25),
        'product_id': fields.integer('Product',),
#        'product_id': fields.many2one('product.product', 'Product', select=True),
#        'ica_mrpjournal': fields.many2one('ica.mrpjournal', 'Journal', select=True),
        'ica_mrpjournal': fields.integer('Mrp Journal', ),
    }
ica_edi_sscc()

class ica_edi_sale_order(osv.osv):
    _name = "sale.order" 
    _inherit = "sale.order"
    _description = "ICA EDI sale.order"
    _columns = {
        'ica_status': 		fields.selection((('s','Standard order'), ('u','ICA order Unconfirmed'),('c','ICA order Confirmed'),('d','ICA order DSPADV') ), 'Status', size=10),
        'date_requested': 	fields.datetime('Date requested',),
        'date_promised': 	fields.datetime('Date promised',),
        'date_delfromica': 	fields.datetime('Date delfromica',),
#        'ica_mrpjournal': fields.many2one('ica.mrpjournal', 'Journal',  readonly=False, required=False, change_default=True,  select=True),
        'ica_mrpjournal': 	fields.integer('Mrp Journal', ),
        'eanreceiver': 		fields.char('EANRECEIVER',size=25,  required=False),
        'eansender': 		fields.char('EANSENDER', size=25, required=False),
        'eandelivery': 		fields.char('EANDELIVERY',size=25, required=False),
        'eanconsignee': 	fields.char('EANCONSIGNEE',size=25, required=False),
        'eanshop': 			fields.char('EANSHOP', 	size=25, required=False),
        'eansupplier': 		fields.char('EANSUPPLIER', size=25, required=False),
        'eanbuyer': 		fields.char('EANBUYER', size=25, required=False),
        'customernumber': 	fields.char('CUSTOMERNUMBER', size=25, required=False),
#        'lass': 			fields.char('Lass', 	size=3, required=False),
#        'pl': 				fields.char('PL', 		size=2, required=False),
#        'utlevomr': 		fields.char('Utlevomr', size=2, required=False),
#        'port': 			fields.char('Port', 	size=2, required=False),
#        'ruta1': 			fields.char('Ruta från',size=3, required=False),
#        'ruta2': 			fields.char('Ruta till',size=3, required=False),
        
#"EANBUYER":    "7301005230007",
#"BUYER_ORGID": "5560210261",
#"EANRECEIVER": "7350031550009",
#"EANSUPPLIER": "7350031550009",
#"CUSTOMERNUMBER": "61036",
#"EANDELIVERY": "7301005230007",
#"EANSHOP":     "7301004017340",
#"EANSENDER":   "7301002000009",
#"EANCONSIGNEE":"7301005230007",
#"BUYER_VATNR": "556021-0261"
    }
    _defaults = {
        'eanreceiver': lambda *a: '',
        'eansender': lambda *a: '',
        'ica_status': lambda *a: 's',
    }
ica_edi_sale_order()


class ica_edi_sale_order_line(osv.osv):
    _name = "sale.order.line" 
    _inherit = "sale.order.line"
    _description = "ICA EDI sale.order.line"
    _columns = {
        'sscc': fields.many2one('ica.sscc', 'SSCC', select=True),
    }
ica_edi_sale_order_line()


class ica_edi_partner(osv.osv):
    _name = "res.partner" 
    _inherit = "res.partner"
    _description = "ICA EDI partner"
    _columns = {
        'consignee_iln': fields.char('Consignee ILN', size=25),
        'shop_iln': fields.char('Shop ILN', size=25),
        'customernumber': fields.char('Customer Number ICA', size=25),
    }
ica_edi_partner()

class ica_edi_product(osv.osv):
    _name = "product.product" 
    _inherit = "product.product"
    _description = "ICA product extensions"
    _columns = {
        'ean14': fields.char('ICA-ean', size=14),
        'su_articlecode': fields.char('Su articlecode',size=14),
#        'packagetype': fields.selection((('34','Returnable box'), ('21','Heatshrinked'),), 'Packagetype', size=20),
        'ica_gln': fields.char('ICA-GLN',size=14),
#        'utskriftsgrupp': fields.selection((('1','1'),('2','2'),('3','3'),('4','4'),('5','5')), 'Utskriftsgrupp', size=1),
        'utskriftsprio': fields.integer('Utskriftsprio', ),              
    }
    _defaults = {
        'packagetype': lambda *a: '34',
    }  
ica_edi_product()

class ica_edi_invoice(osv.osv):
    _name = "account.invoice" 
    _inherit = "account.invoice"
    _description = "ICA invoice extensions"
    _columns = {
        'ica_mrpjournal': fields.integer('Mrp Journal', ),
        'ica_invoice_id': fields.integer('ica.invoice',),
    }
    _defaults = {
        'ica_invoice_id': lambda *a: 0,
        'ica_mrpjournal': lambda *a: 0,
    }   
ica_edi_invoice()

class sale_order_tax(osv.osv):
    _name = "sale.order.tax" 
    _description = "Tax on saleorder-lines"
    _columns = {
        'order_line_id':    fields.integer('Orderline ID',),
        'tax_id':           fields.integer('Tax ID',),
    }
sale_order_tax()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
