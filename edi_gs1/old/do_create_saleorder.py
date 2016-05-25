#!/usr/bin/python
# Create saleorder from imported ICA-order
#
#
# b) ica.mrpjournal.state has been changed to 'b' (Bekrafta) by a user
#    This run works with ica.import_order.status == n (Unconfirmed) and ica.import_order.mrpjournal_id > 0
#    Create sale.order and set ica.import_order.saleorder_id and ica.import_order.status = 'c' and
#    ica.mrp_journal.saleorder_imported


# This code needs a trigger in the database
# CREATE RULE ica_sale_order_tax AS ON INSERT TO sale_order_line DO INSERT INTO sale_order_tax (order_line_id, tax_id) VALUES (lastval(), 11); 
# tax_id are id for Moms 25%



import xmlrpclib
import datetime
import json
from optparse import OptionParser

#parser = OptionParser(xusage="%prog --database=DBNAME --username=USER --password=PWD --server=SERVERNAME")
parser = OptionParser()
parser.add_option("-d", "--database", dest="dbname",help="use database DATABASE")
parser.set_defaults(dbname='test_aw')
parser.add_option("-j", "--journal", dest="journal",help="use journal JOURNAL")
parser.set_defaults(journal=0)
parser.add_option("--noupdate", dest="noupdate",help="dont update mrpjournal")
parser.set_defaults(noupdate=0)
parser.add_option("-u", "--username", dest="username",help="use user USERNAME", default="admin")
parser.set_defaults(username='admin')
parser.add_option("-p", "--password", dest="pwd",help="use password PASSWORD", default="admin")
parser.set_defaults(pwd='admin')
parser.add_option("-s", "--server", dest="servername",help="use server http://servername:port%s ")
parser.set_defaults(servername='http://localhost:8069%s')

(options, args) = parser.parse_args()


#username = 'admin'  # username and password will change in the future
pwd = options.pwd
dbname = options.dbname  # This is the test-database for now
journal = options.journal
servername = "http://erp.greenvision.nu:8069%s"
#servername = "http://localhost:8069%s"

#  Open ERP listens at port 8069
sock_common = xmlrpclib.ServerProxy (options.servername % "/xmlrpc/common")
uid = sock_common.login(options.dbname, options.username, options.pwd)
sock = xmlrpclib.ServerProxy(options.servername % "/xmlrpc/object", use_datetime=True)


today = datetime.datetime.today()

# Just a search to check order_ids is growing
mrpjournal = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'read',[journal])   # Use Partner and todays date as key
if mrpjournal[0]['status'] == 's':

    order_ids = sock.execute(dbname, uid, pwd, 'ica.import_order', 'search',[("status","=","n"),("mrpjournal_id","=",journal)])  # c = confirmed (imported) order in OpenERP u = Unconfirmed order in OpenERP

    print "order_ids", order_ids

    if order_ids:

        for order_record in sock.execute(dbname, uid, pwd, 'ica.import_order', 'read', order_ids):
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
            partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANDELIVERY'])])   # Use EANDELIVERY as key in partner
            if not partner_id:
                partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANDELIVERY'], 'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANDELIVERY']})
                partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANDELIVERY'])])   # Use EANDELIVERY as key in partner
            partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id[0])
            addr =  {}
            for addr_rec in sock.execute(dbname, uid, pwd, 'res.partner.address', 'read', partner['address'] ):
                addr[addr_rec['type']] = addr_rec
            adress_order    = addr.get('default',{'id': 1})
            adress_invoice  = addr.get('invoice',addr.get('default',{'id': 1}))
            adress_shipping = addr.get('delivery',addr.get('default',{'id': 1}))

            # Buyer / ICA
            buyer_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANBUYER'])])   # Use EANSHOP as key in partner
            if not buyer_id:
                buyer_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANBUYER'],  'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANBUYER']})
                buyer_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANBUYER'])])   # Use EANSHOP as key in partner
            buyer = sock.execute(dbname, uid, pwd, 'res.partner', 'read', buyer_id[0])

            # Sender / ICA
            sender_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANSENDER'])])   # Use EANSHOP as key in partner
            if not sender_id:
                sender_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANSENDER'],  'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANSENDER']})
                sender_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANSENDER'])])   # Use EANSHOP as key in partner
            sender = sock.execute(dbname, uid, pwd, 'res.partner', 'read', sender_id[0])

            # Create sale.order when mrpjournal are marked with state = s for orders in that journal
            if order_record['saleorder_id'] == 0:
                print "Skapa sale.order", partner['id']
                # print mrpjournal, order, "Saleorder"
                saleorder_id = sock.execute(dbname, uid, pwd, 'sale.order', 'create', {
                    'partner_id':       partner['id'],
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
                    'pricelist_id':     partner['property_product_pricelist'][0],
                    'ica_mrpjournal':   mrpjournal[0]['id'],
                    'eansender':        order['HEA']['EANSENDER'],
                    'eanreceiver':      order['HEA']['EANRECEIVER'],
                    'eandelivery':      order['HEA']['EANDELIVERY'],
                    'eanconsignee':     order['HEA']['EANCONSIGNEE'],
                    'eanshop':          order['HEA']['EANSHOP'],
                    'eanbuyer':         order['HEA']['EANBUYER'],
                    'eansupplier':      order['HEA']['EANSUPPLIER'],
                    'customernumber':   order['HEA']['CUSTOMERNUMBER'],
                    'state':            'done',
                    })
                    
                    
    #            saleorder = sock.execute(dbname, uid, pwd, 'sale.order', 'read', saleorder_id)

    #            print "Saleorder_id ", saleorder_id, order['HEA']['LIN']

                for line in order['HEA']['LIN']:
                    # Product
                    product_id = sock.execute(dbname, uid, pwd, 'product.product', 'search',[("ean14","=",line['EAN'])])   # Use EAN as key in product

                    if not product_id:                  # Create missing products
                        partner_id = sock.execute(dbname, uid, pwd, 'product.product', 'create', {'su_articlecode': line['SU_ARTICLECODE'], 'ean14': line['EAN'], 'name': 'Saknad produkt %s'  % line['SU_ARTICLECODE'], 'categ_id': 1,})
                        product_id = sock.execute(dbname, uid, pwd, 'product.product', 'search',[("ean14","=",line['EAN'])]) 

                    product = sock.execute(dbname, uid, pwd, 'product.product', 'read', product_id[0])
     
     
                    
                    saleorderline_ids = sock.execute(dbname, uid, pwd, 'sale.order.line', 'create', {
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
     #                   'tax_id': fields.many2many('account.tax', 'sale_order_tax', 'order_line_id', 'tax_id', 'Taxes', readonly=True, states={'draft':[('readonly',False)]}),
                        'th_weight':        0,
                        'type':             'make_to_stock',
                        'tax_id':           product['taxes_id'],
                    })

                    for tax in product['taxes_id']:
                        saleordertax_id = sock.execute(dbname, uid, pwd, 'sale.order.tax', 'create', {'order_line_id': saleorderline_ids, 'tax_id': tax})
                        

                # Mark import_order imported / Confirmed
                # Knyt ica.import_order till mrpjournal
                order_marked = sock.execute(dbname, uid, pwd, 'ica.import_order', 'write', order_record['id'], {'status': 'c', 'saleorder_id': saleorder_id,})
                if not options.noupdate:
                    mrpjournal_marked = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'write', mrpjournal[0]['id'], {'saleorder_imported': today.strftime('%Y-%m-%d %H:%M')})
                
    else:
        print "Nothing to create\n"
