
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
# 2010-10-08 anders.wallenquist@vertel.se  Hämta och lagra transportinformation

import wizard
import pooler
import os
import json
import netsvc
import datetime
from osv import fields, osv
from tools.translate import _

def check_ordernumber(cr,uid,ord_nr):
    logger = netsvc.Logger()
    doubles = []
    today = datetime.datetime.today()
    week = today - datetime.timedelta(days=7)

    for nr in ord_nr:
        ids = pooler.get_pool(cr.dbname).get('sale.order').search(cr,uid,[("client_order_ref","=",nr),("date_order",">",week.strftime("%Y-%m-%d"))])
        #logger.notifyChannel("warning", netsvc.LOG_WARNING,"check_ordernumber '%s' %s %s." % (ids,nr,week.strftime("%Y-%m-%d")))
        if len(ids)>1:  # First occurance are our order today
            doubles.append(nr)

    return doubles
    

class ica_mrpjournal_do_import_order_sale(wizard.interface):
    

    
    def _do_create_saleorder(self, cr, uid, data, context):
        today = datetime.datetime.today()
        order_cr = pooler.get_pool(cr.dbname).get('sale.order')

        partner_cr =  pooler.get_pool(cr.dbname).get('res.partner')
        address_cr =  pooler.get_pool(cr.dbname).get('res.partner.address')
        product_cr =  pooler.get_pool(cr.dbname).get('product.product')
        sale_order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        line_cr = pooler.get_pool(cr.dbname).get('sale.order.line')
        tax_cr = pooler.get_pool(cr.dbname).get('sale.order.tax')
        		
        import_order_cr = pooler.get_pool(cr.dbname).get('ica.import_order')
        
        logger = netsvc.Logger()
        
        ord_nr = []
        		
        for jid in data['ids']:  # Om det är flera markerade dagjournaler
            journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal').read(cr,uid,jid) 
#            raise osv.except_osv(_('Journal'), _('Data\n%s') % (journal))

            # Just a search to check order_ids is growing
            print journal
            if journal['status'] == 'i':  # Journal ready for create saleorder

                import_order_ids = import_order_cr.search(cr, uid, [("status","=","n"),("mrpjournal_id","=",jid)])

                print "import_order_ids", import_order_ids

                if import_order_ids:
                
                    for order_record in import_order_cr.read(cr, uid, import_order_ids):
                        order = json.loads(order_record['blob'])
                        
                        # Partner / shop
                        #partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANSHOP'])])   # Use EANSHOP as key in partner
                        #if not partner_id:
                        #    partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANSHOP'], 'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANSHOP']})
                        #    partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANSHOP'])])   # Use EANSHOP as key in partner
                        #partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id[0])
                        #addr =  {}
                        #for addr_rec in sock.execute(dbname, uid, pwd, 'res.partner.address', 'read', partner['address'] ):
                        #    addr[addr_rec['type']] = addr_rec
                        #adress_order    = addr.get('default',{'id': 1})
                        #adress_invoice  = addr.get('invoice',addr.get('default',{'id': 1}))
                        #adress_shipping = addr.get('delivery',addr.get('default',{'id': 1}))
                        # Partner / shop
                        partner_id = partner_cr.search(cr, uid, [("shop_iln","=",order['HEA']['EANDELIVERY'])])   # Use EANDELIVERY as key in partner
                        if not partner_id:
                            partner_id = partner_cr.create(cr, uid,  { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANDELIVERY'], 'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANDELIVERY']})
                            partner_id = partner_cr.search(cr, uid, [("shop_iln","=",order['HEA']['EANDELIVERY'])])   # Use EANDELIVERY as key in partner
                        partner = partner_cr.read(cr, uid,  partner_id)
                        print "partner ", partner
                        print "address", partner[0]['address']
                        addr =  {}
                        for addr_rec in address_cr.read(cr, uid, partner[0]['address'] ):
                            addr[addr_rec['type']] = addr_rec
                        adress_order    = addr.get('default',{'id': 1})
                        adress_invoice  = addr.get('invoice',addr.get('default',{'id': 1}))
                        adress_shipping = addr.get('delivery',addr.get('default',{'id': 1}))

                        # Buyer / ICA
                        buyer_id = partner_cr.search(cr, uid, [("shop_iln","=",order['HEA']['EANBUYER'])])   # Use EANSHOP as key in partner
                        if not buyer_id:
                            buyer_id = partner_cr.create(cr, uid,  { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANBUYER'],  'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANBUYER']})
                            buyer_id = partner_cr.search(cr, uid, [("shop_iln","=",order['HEA']['EANBUYER'])])   # Use EANSHOP as key in partner
                        buyer = partner_cr.read(cr, uid, buyer_id)

                        # Sender / ICA
                        sender_id = partner_cr.search(cr, uid, [("shop_iln","=",order['HEA']['EANSENDER'])])   # Use EANSHOP as key in partner
                        if not sender_id:
                            sender_id = partner_cr.create(cr, uid,  { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANSENDER'],  'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANSENDER']})
                            sender_id = partner_cr.search(cr, uid, [("shop_iln","=",order['HEA']['EANSENDER'])])   # Use EANSHOP as key in partner
                        sender = partner_cr.read(cr, uid,  sender_id)

                        # Create sale.order when mrpjournal are marked with state = s for orders in that journal
                        if order_record['saleorder_id'] == 0:
                            print "Skapa sale.order", partner[0]['id']
                       
                            ord_nr.append(order['HEA']['ORDERNUMBER'])
                            # print mrpjournal, order, "Saleorder"
                            saleorder_id = sale_order_cr.create(cr, uid,  {
                                'partner_id':       buyer[0]['id'],
                                'ica_status':       'u',
                                'client_order_ref': order['HEA']['ORDERNUMBER'],
                                'origin':           order['HEA']['ORDERNUMBER'],
                                'date_order':       order['HEA']['ORDERDATE'],
                                'date_requested':   order['HEA']['DELDATESTORE'],
                                'date_promised':    order['HEA']['DELDATELE'],
                                'date_delfromica':  order['HEA']['SHIPDATEFROMLE'],  
                                'partner_order_id': adress_order['id'],            
                                'partner_invoice_id':  adress_invoice['id'],
                                'partner_shipping_id': adress_shipping['id'],
                                'pricelist_id':     partner[0]['property_product_pricelist'][0],
                                'ica_mrpjournal':   journal['id'],
                                'eansender':        order['HEA']['EANSENDER'],
                                'eanreceiver':      order['HEA']['EANRECEIVER'],
                                'eandelivery':      order['HEA']['EANDELIVERY'],
                                'eanconsignee':     order['HEA']['EANCONSIGNEE'],
                                'eanshop':          order['HEA']['EANSHOP'],
                                'eanbuyer':         order['HEA']['EANBUYER'],
                                'eansupplier':      order['HEA']['EANSUPPLIER'],
                                'customernumber':   order['HEA']['CUSTOMERNUMBER'],
                                # Retrieve freigh information
                                #"FREIGHTLABEL1": "03/05/527/02/005/011", 
                                'utlevomr':			order['HEA']['FREIGHTLABEL1'].split('/')[0],
                                'port':				order['HEA']['FREIGHTLABEL1'].split('/')[1],
                                'lass':				order['HEA']['FREIGHTLABEL1'].split('/')[2],
                                'pl':				order['HEA']['FREIGHTLABEL1'].split('/')[3],
                                'ruta1':			order['HEA']['FREIGHTLABEL1'].split('/')[4],
                                'ruta2':			order['HEA']['FREIGHTLABEL1'].split('/')[5],

                                'state':            'progress',
                                })
                                
                                
                #            saleorder = sock.execute(dbname, uid, pwd, 'sale.order', 'read', saleorder_id)

                #            print "Saleorder_id ", saleorder_id, order['HEA']['LIN']

                            for line in order['HEA']['LIN']:
                                # Product
                                product_id = product_cr.search(cr, uid, [("ean14","=",line['EAN'])])   # Use EAN as key in product

                                if not product_id:                  # Create missing products
                                    logger.notifyChannel("do_create_saleorder", netsvc.LOG_WARNING,"Missing product '%s' '%s'  ." % (line['SU_ARTICLECODE'],line['EAN']))
                                    cr.rollback()
                                    raise osv.except_osv(_('Saknad produkt'), _('%s %s') % (line['SU_ARTICLECODE'],line['EAN']))
                                    return {}
                                    #partner_id = product_cr.create(cr, uid,  {'su_articlecode': line['SU_ARTICLECODE'], 'ean14': line['EAN'], 'name': 'Saknad produkt %s'  % line['SU_ARTICLECODE'], 'categ_id': 1,})
                                    #product_id = product_cr.search(cr, uid, [("ean14","=",line['EAN'])]) 

                                product = product_cr.read(cr, uid,  product_id[0])
                                print product_id, product
                                tax_id = int(product['taxes_id'][0]);
                                print "tax_id", tax_id
                 
                                saleorderline_id = line_cr.create(cr, uid, {
                #                    'address_allotment_id': ,
                                    'delay':            0.0,
                                    'discount':         0.0,
                                    'invoiced':         0,
                 #                   'invoice_lines': fields.many2many('account.invoice.line', 'sale_order_line_invoice_rel', 'order_line_id', 'invoice_id', 'Invoice Lines', readonly=True),
                 #                   'move_ids': fields.one2many('stock.move', 'sale_line_id', 'Inventory Moves', readonly=True),
                                    'name':             product['name'],
                                    'notes':            '',
                #                    'number_packages': fields.function(_number_packages, method=True, type='integer', string='Number Packages'),
                                    'order_id':         saleorder_id,
                #                    'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', string='Customer')
                #                    'price_net': fields.function(_amount_line_net, method=True, string='Net Price', digits=(16, int(config['price_accuracy']))),
                #                    'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal', digits=(16, int(config['price_accuracy']))),
                #                    'price_unit':       product['uos_id'],
                                    'price_unit':       product['list_price'],
                #                    'procurement_id': fields.many2one('mrp.procurement', 'Procurement'),
                                    'product_id':       product['id'],
                                    'product_packaging': 0,
                    #                    'product_uom':      product['list_price'],
                                    'product_uom':      product['uom_id'][0],
                                    'product_uom_qty':  line['QTY_ORDERED'],
                                    'product_uos':      1,
                                    'product_uos_qty':  1,
                #                    'property_ids': fields.many2many('mrp.property', 'sale_order_line_property_rel', 'order_id', 'property_id', 'Properties', readonly=True, states={'draft':[('readonly',False)]}),
                                    'sequence':         10,
                                    'state':            'confirmed',
                                    'th_weight':        0,
                                    'type':             'make_to_stock',
                                    'tax_id':           product['taxes_id'],
                                })

                                print "Sale order line id", saleorderline_id
                                
                                for tax in product['taxes_id']:
                                #    saleordertax_id = tax_cr.create(cr, uid,  {'order_line_id': saleorderline_ids, 'tax_id': int(tax)})                            
                                    cr.execute('INSERT INTO sale_order_tax ("order_line_id", "tax_id", "create_uid", "create_date") VALUES (' + str(saleorderline_id) + ',' + str(tax) + ', ' + str(uid) + ', ' + today.strftime("'%Y-%m-%d %H:%M'") + ' )')

                            # Mark import_order imported / Confirmed
                            # Knyt ica.import_order till mrpjournal
                            # Create tax-lines
                            #print sale_order_cr.amount_tax(cr,uid,saleorder_id)
                            
                            order_marked = import_order_cr.write(cr, uid,  order_record['id'], {'status': 'c', 'saleorder_id': saleorder_id,})
                            pooler.get_pool(cr.dbname).get('ica.mrpjournal').write(cr, uid, jid, {'saleorder_imported': today.strftime('%Y-%m-%d %H:%M'), 'status': 's' })
                else:
                            pooler.get_pool(cr.dbname).get('ica.mrpjournal').write(cr, uid, jid, {'saleorder_imported': today.strftime('%Y-%m-%d %H:%M'), 'status': 's' })

        cr.commit()

        doubles = check_ordernumber(cr,uid,ord_nr)  # Kontrollerar orderdubletter
        if len(doubles) > 0:
            logger.notifyChannel("warning", netsvc.LOG_WARNING,"Orderdubletter '%s'  ." % (doubles))
            raise osv.except_osv(_('Dublettorder'), _('Dessa ordernumber (Client ref) finns redan\n%s') % (doubles))

# Kontroll order_requested före dagens datum, meddela ordernummer för manuell kontroll

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
