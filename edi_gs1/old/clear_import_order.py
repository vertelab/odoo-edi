#!/usr/bin/python

# Clear already used ica.import_order for more testing

import xmlrpclib
import datetime
import json

username = 'admin'  # username and password will change in the future
pwd = 'admin'
dbname = 'wftest'  # This is the test-database for now
#servername = "http://erp.greenvision.nu:8069%s"
servername = "http://localhost:8069%s"

#  Open ERP listens at port 8069
sock_common = xmlrpclib.ServerProxy (servername % "/xmlrpc/common")
uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy(servername % "/xmlrpc/object", use_datetime=True)

    
res = sock.execute(dbname, uid, pwd, 'ica.import_order', 'write', sock.execute(dbname, uid, pwd, 'ica.import_order', 'search',[]),{'status': 'n','mrpjournal_id': 0,'saleorder_id': 0 })

#res = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'unlink', sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'search',[]))

#res = sock.execute(dbname, uid, pwd, 'sale.order', 'write', sock.execute(dbname, uid, pwd, 'sale.order', 'search',[]), {'state': 'draft' } )

#res = sock.execute(dbname, uid, pwd, 'sale.order.line', 'write', sock.execute(dbname, uid, pwd, 'sale.order.line', 'search',[]), {'state': 'draft' } )

#res = sock.execute(dbname, uid, pwd, 'sale.order.line', 'unlink', sock.execute(dbname, uid, pwd, 'sale.order.line', 'search',[]))
#res = sock.execute(dbname, uid, pwd, 'sale.order', 'unlink', sock.execute(dbname, uid, pwd, 'sale.order', 'search',[]))


#res = sock.execute(dbname, uid, pwd, 'account.invoice.tax', 'unlink', sock.execute(dbname, uid, pwd, 'account.invoice.tax', 'search',[]))
#res = sock.execute(dbname, uid, pwd, 'account.invoice.line', 'unlink', sock.execute(dbname, uid, pwd, 'account.invoice.line', 'search',[]))
#res = sock.execute(dbname, uid, pwd, 'account.invoice', 'unlink', sock.execute(dbname, uid, pwd, 'account.invoice', 'search',[]))

#res = sock.execute(dbname, uid, pwd, 'ica.ordrsp', 'unlink', sock.execute(dbname, uid, pwd, 'ica.ordrsp', 'search',[]))
#res = sock.execute(dbname, uid, pwd, 'ica.dspadv', 'unlink', sock.execute(dbname, uid, pwd, 'ica.dspadv', 'search',[]))
#res = sock.execute(dbname, uid, pwd, 'ica.invoice', 'unlink', sock.execute(dbname, uid, pwd, 'ica.invoice', 'search',[]))

