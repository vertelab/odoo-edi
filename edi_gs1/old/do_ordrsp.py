#!/usr/bin/python

# Create ORDRSP from confirmed sale.order

import xmlrpclib
import datetime
import json
from optparse import OptionParser

#parser = OptionParser(xusage="%prog --database=DBNAME --username=USER --password=PWD --server=SERVERNAME")
parser = OptionParser()
parser.add_option("-d", "--database", dest="dbname",help="use database DATABASE")
parser.set_defaults(dbname='test_aw')
parser.add_option("-j", "--journal", dest="journal",help="use journal JOURNAL")
parser.set_defaults(journal=1)
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
#servername = "http://erp.greenvision.nu:8069%s"
#servername = "http://localhost:8069%s"

#  Open ERP listens at port 8069
sock_common = xmlrpclib.ServerProxy (options.servername % "/xmlrpc/common")
uid = sock_common.login(options.dbname, options.username, options.pwd)
sock = xmlrpclib.ServerProxy(options.servername % "/xmlrpc/object", use_datetime=True)

today = datetime.datetime.today()

# Just a search to check order_ids is growin
mrpjournal_ids = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'search',[("status","=",'o'),("saleorder_ordrsp",'=',False),("id",'=',journal)])   # Use Partner and todays date as key
print mrpjournal_ids
if mrpjournal_ids:
    order_ids = sock.execute(dbname, uid, pwd, 'sale.order', 'search',[("ica_mrpjournal","in", mrpjournal_ids )])  # c=confirmed order for response in OpenERP u = Unconfirmed order in OpenERP d = Order for dispatch
print order_ids

if order_ids:

    for order_record in sock.execute(dbname, uid, pwd, 'sale.order', 'read', order_ids):
        
        print order_record['partner_id']
        # Partner
        partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', order_record['partner_id'][0])

        ordrsp = {
            'HEA': {
                'MESSAGETYPE':      'ordrsp',
                'EANSENDER':        order_record['eanreceiver'],
                'EANRECEIVER':      order_record['eansender'],
                'TEST':             '0',
                'ORDERRESNUMBER':	order_record['name'],	
                'ORDERNUMBER':	    order_record['origin'],	
                'ORDERRESDATE':	    datetime.datetime.strptime(order_record['date_order'],'%Y-%m-%d').strftime("%Y%m%d"),
                'DELDATESTORE':	    datetime.datetime.strptime(order_record['date_requested'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),	
                'DELDATELE':	    datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),	
                'EANBUYER':	        order_record['eanbuyer'],
                'EANSUPPLIER':	    order_record['eansupplier'],
                'EANCONSIGNEE':	    order_record['eanconsignee'],	
                'EANSHOP':	        order_record['eanshop'],
                'CUSTOMERNUMBER':	order_record['customernumber'],
                'LIN': [],
            }
        }

        lines_ids = sock.execute(dbname, uid, pwd, 'sale.order.line', 'search',[("order_id","=",order_record['id'])])
        olines = sock.execute(dbname, uid, pwd, 'sale.order.line', 'read', lines_ids) 
        for line in olines:            
            # Product
            product = sock.execute(dbname, uid, pwd, 'product.product', 'read',line['product_id'][0])  
            
            if not product['code']:
                product['code'] = product['ean14']

            ordrsp['HEA']['LIN'].append({
                'NUMBER':           line['sequence'],
                'EAN':              product['ean14'],
                'SU_ARTICLECODE':	product['code'],
#                'BATCHNUMBER':      '',	
#                'EANSUBS':          '',	
#                'SU_ARTICLECODESUBS': '',	
                'QTY_ORDERED':	    line['product_uom_qty'], # Borde vi inte spara bestallt?
                'QTY_AVAILABLE':    line['product_uom_qty'],
                'NETPRICE':         product['lst_price'],	
            })
        
        # Mark sale.order ready for dispatch
        ordrsp_delivered = sock.execute(dbname, uid, pwd, 'ica.ordrsp', 'create', {'mrpjournal_id': mrpjournal_ids[0], 'saleorder_id': order_record['id'],'status': 'c','blob': json.dumps(ordrsp)})
        order_marked = sock.execute(dbname, uid, pwd, 'sale.order', 'write', order_ids, {'ica_status': 'd',})        
        
    if not options.noupdate:
        mrpjournal_marked = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'write', mrpjournal_ids, {'saleorder_ordrsp': today.strftime('%Y-%m-%d %H:%M')})
                
    
else:
    print "Nothing to respond\n"
