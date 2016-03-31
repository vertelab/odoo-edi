#!/usr/bin/python

# Test createing sale.order

import xmlrpclib

username = 'admin'  # username and password will change in the future
pwd = 'admin'
dbname = 'test_aw06'  # This is the test-database for now
#servername = "http://erp.greenvision.nu:8069%s"
servername = "http://localhost:8069%s"

#  Open ERP listens at port 8069
sock_common = xmlrpclib.ServerProxy (servername % "/xmlrpc/common")
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy(servername % "/xmlrpc/object", use_datetime=True)

# Partner / shop
partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', [121])

print partner[0]['property_product_pricelist'][0]

saleorder_id = sock.execute(dbname, uid, pwd, 'sale.order', 'create', {
    'partner_id':       partner[0]['id'],    
    'partner_order_id': 1,            
    'partner_invoice_id':  1,
    'partner_shipping_id': 1,
    'pricelist_id':      partner[0]['property_product_pricelist'][0],
    
    
    'client_order_ref':  'Ordernummer',
    'origin': 'origin',
    
    'date_order':       '20100419',
    'date_requested':   '20100419',
    'date_promised':    '20100419',
    'date_delfromica':  '20100419',  

    'ica_mrpjournal':   93,
    })
 
    
saleorderline_ids = sock.execute(dbname, uid, pwd, 'sale.order.line', 'create', {
        'product_id':       1,
        'product_uom_qty':  35,
        'order_id':         saleorder_id,
        'product_uom':      1,
        'price_unit':       1,
        'name':             'name',                    
    })
    
print saleorder_id,sock.execute(dbname, uid, pwd, 'sale.order', 'read', saleorder_id)
