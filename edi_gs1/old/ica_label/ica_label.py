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

class ica_label(osv.osv):
    _name = "ica.label"
    _description = "ICA label"
    _columns = {
        'completed':        fields.integer('Completed', ),
        'date_printed':     fields.date('Date printed', ),
        'customernumber':   fields.char('CUSTOMERNUMBER', size=25),
        'date_order':       fields.date('Date order', ),
        'deldateshop':      fields.date('DELDATESHOP',),
        'desadvnumber':		fields.char('DESADVNUMBER', size=25),	
        'dspadv_id':        fields.integer('DspAdv', ),
#        'dspadv_id': fields.many2one('ica.dspadv','ICA EDI', select=True),
        'eanbuyer':	        fields.char('EANBUYER', size=25),
        'eanconsignee':     fields.char('EANCONSIGNEE', size=25),
        'eandelivery':	    fields.char('EANDELIVERY',size=25),                            
        'eanreceiver':      fields.char('EANRECEIVER', size=25),
        'eansender':        fields.char('EANSENDER', size=25),
        'eansupplier':      fields.char('EANSUPPLIER', size=25),
        'eanshop':          fields.char('EANSHOP', size=25),
        'estdeldate':	    fields.date('ESTDELDATE',),
        'ica_mrpjournal':   fields.integer('Mrp Journal', ),
#        'ica_mrpjournal': fields.many2one('ica.mrpjournal', 'Journal', select=True),
        'line_id':          fields.many2one('sale.order.line','Orderline', select=True),
        'ordernumber':	    fields.char('Ordernumber',size=25),
        'order_id':         fields.many2one('sale.order','Order',select=True),
        'pacnumber':        fields.integer('Pacnumber'),
        'partner_id':       fields.many2one('res.partner', 'Customer', select=True),
#        'product_id': fields.integer('Product',),
        'product_id':       fields.many2one('product.product', 'Product', select=True),
        'sscc':             fields.char("SSCC",			size=18),
        'transportnumber':  fields.integer('Transportnumber', ),
        'typeofpackage':    fields.char("Type of package",size=3),
        'utskriftsgrupp': 	fields.char('Utskriftsgrupp', size=1),
        'utskriftsprio': 	fields.integer('Utskriftsprio', 	required=False),
        'lass': 			fields.char('Lass', 		size=3, required=False),
        'pl': 				fields.char('PL', 			size=2, required=False),
        'utlevomr': 		fields.char('Utlevomr', 	size=2, required=False),
        'port': 			fields.char('Port', 		size=2, required=False),
        'ruta1': 			fields.char('Ruta från', 	size=3, required=False),
        'ruta2': 			fields.char('Ruta till', 	size=3, required=False),     
        'plockid': 			fields.char('Plock ID',		size=5, required=False),     
        'bundle_qty':		fields.integer('Antal Kolli', 		required=False),
        'pallet_no':		fields.integer('Pall nr', 			required=False),

    }
    _defaults = {
        'completed': lambda *a: False,
    }
ica_label()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
