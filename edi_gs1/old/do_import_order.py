#!/usr/bin/python
# Import ICA-order to sale.older
#
# States of imported ica.import_order
# a) BOTS has just delivered ICA-orders, this run will create a new 
#    ica.mrpjournal all ica.import_order will be connected to the journal
#    This run works with ica.import_order.status == n (Unconfirmed)  and ica.import_order.mrpjournal_id == 0
#    set ica.mrpjournal.state to 'i' (Inkommen) and ica.import_order.mrpjournal_id
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
#servername = "http://erp.greenvision.nu:8069%s"
#servername = "http://localhost:8069%s"

#  Open ERP listens at port 8069
sock_common = xmlrpclib.ServerProxy (options.servername % "/xmlrpc/common")
print options.dbname, options.username, options.pwd
uid = sock_common.login(options.dbname, options.username, options.pwd)
sock = xmlrpclib.ServerProxy(options.servername % "/xmlrpc/object", use_datetime=True)


today = datetime.datetime.today()

# Just a search to check order_ids is growing
order_ids = sock.execute(dbname, uid, pwd, 'ica.import_order', 'search',[("status","=","n"),('mrpjournal_id','=',0)])  # c = confirmed (imported) order in OpenERP u = Unconfirmed order in OpenERP

print "order_ids", order_ids

if order_ids:

    for order_record in sock.execute(dbname, uid, pwd, 'ica.import_order', 'read', order_ids):
        order = json.loads(order_record['blob'])
        
        # Partner / shop
        partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANSHOP'])])   # Use EANSHOP as key in partner
        if not partner_id:
            partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'create', { 'consignee_iln':  order['HEA']['EANCONSIGNEE'], 'shop_iln': order['HEA']['EANSHOP'], 'customernumber': order['HEA']['CUSTOMERNUMBER'], 'name': 'Saknad kund %s' % order['HEA']['EANSHOP']})
            partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("shop_iln","=",order['HEA']['EANSHOP'])])   # Use EANSHOP as key in partner
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


        # Mrp Journal one for each day and Buyer
#        mrpjournal_id = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'search',[("partner_id","=",sender['id']),("datum","=", today.strftime('%Y-%m-%d %H:%M'))])   # Use Partner and todays date as key
        mrpjournal_id = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'search',[("datum","=", today.strftime('%Y-%m-%d %H:%M'))])   # Use todays date as key
        if not mrpjournal_id:
            mrpjournal_id = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'create', { 
                'partner_id':   buyer['id'],
                'datum':        today.strftime('%Y-%m-%d %H:%M'),
                'status':       'i',
                })


        mrpjournal = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'read', mrpjournal_id);
        if len(mrpjournal) == 1:  # newly created mrpjournals gives different structure 
            mrpjournal=mrpjournal[0]

        print "Mrp_status",mrpjournal['status'],order_record['mrpjournal_id'],mrpjournal['id'],order_record['saleorder_id']        

        order_marked = sock.execute(dbname, uid, pwd, 'ica.import_order', 'write', order_record['id'], {'mrpjournal_id': mrpjournal['id']}) 
            
else:
    print "Nothing to import\n"
