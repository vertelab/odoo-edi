#!/usr/bin/python

# Create DSPADV from confirmed sale.order

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


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

def makeSSCC(nr):
# http://gs1.se/sv/GS1-systemet/Berakna-kontrollsiffra/Sa-beraknas-kontrollsiffran/
    prefix = 3
    ftgnr  = 7350031

    sscc = str(prefix) + str(ftgnr) + '%09d' % nr
    # 37350031000000190
    first  = sscc[::-2]  # Varannan siffra fran hoger 010003033
    second = sscc[1::2]   # Resten av siffrorna  

    first_tot = 0
    second_tot = 0

    for i in first:
        first_tot += int(i)
    first_tot = first_tot * 3

    for i in second:
        second_tot += int(i)
        
    checksum = 10 - (first_tot + second_tot) % 10
    if checksum == 10 or checksum < 0:
        checksum = 0
    sscc = sscc + "%1d" % checksum

    return sscc


# Mrp Journals in status l not made, sale.orders bound to those journals
#mrpjournal_ids = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'search',[("status","=",'l'),("saleorder_dspadv",'=',False)]) 
mrpjournal_ids = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'search',[("status","=",'l'),("saleorder_dspadv",'=',False),('id','=',journal)]) 
print mrpjournal_ids
if mrpjournal_ids:
    mrpjournal = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'read',mrpjournal_ids)
    order_ids = sock.execute(dbname, uid, pwd, 'sale.order', 'search',[("ica_mrpjournal","in", mrpjournal_ids )])

    if order_ids:
        print order_ids
        for order_record in sock.execute(dbname, uid, pwd, 'sale.order', 'read', order_ids):
			# Partner
            partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', order_record['partner_id'][0])

            dspadv = {
				'HEA': {
					'MESSAGETYPE':      'desadv01',
                    'EANSENDER':        order_record['EANRECEIVER'],
                    'EANRECEIVER':      order_record['EANSENDER'],
					'TEST':             '0',
					'DESADVNUMBER':		order_record['name'],	
					'DESADVDATE':	    datetime.datetime.strptime(order_record['date_order'],'%Y-%m-%d').strftime("%Y%m%d"),
					'ESTDELDATE':	    datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
					'EANBUYER':	        '7301005140009',
					'EANSHIPPER':	    '7350031550009',    
					'EANDELIVERY':	    partner['consignee_iln'],	
					'PAC': [],                
				}
            }

            pacnumber = 0
			# One PAC for each sale.order.line and each product_oum_qty 
            for line in sock.execute(dbname, uid, pwd, 'sale.order.line', 'read', sock.execute(dbname, uid, pwd, 'sale.order.line', 'search',[("order_id","=",order_record['id'])])):

				# Product
                product = sock.execute(dbname, uid, pwd, 'product.product', 'read',line['product_id'][0])  


                q=1
                while q<=line['product_uom_qty']:
                    q+=1
                    edi_record = sock.execute(dbname, uid, pwd, 'ica.edi', 'read', 1, ['next_sscc'])
                    if not edi_record['next_sscc']:
                        edi_record['next_sscc']=1
                        res = sock.execute(dbname, uid, pwd, 'ica.edi', 'create', {'next_sscc': edi_record['next_sscc']})
                    res = sock.execute(dbname, uid, pwd, 'ica.edi', 'write', 1, {'next_sscc': edi_record['next_sscc']+1})

                    sscc = makeSSCC(edi_record['next_sscc'])
                    sscc_id = sock.execute(dbname, uid, pwd, 'ica.sscc', 'create', {
                        'sscc':             sscc,
                        'line_id':          line['id'],
                        'EANSENDER':        order_record['EANRECEIVER'],
                        'EANRECEIVER':      order_record['EANSENDER'],
                        'EANSHOP':			partner['shop_iln'],
                        'CUSTOMERNUMBER':   partner['customernumber'],	
                        'DELDATESHOP':      datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
                        'product_id':       product['id'],
                        'ica_mrpjournal':   order_record['ica_mrpjournal'],
                        })
                    
                    pacnumber += 1
                    dspadv['HEA']['PAC'].append({
                        'PACNUMBER':        pacnumber,
                        'SSCC':				sscc,
                        'ORDERNUMBER':		order_record['name'],
                        'EANCONSIGNEE':     partner['consignee_iln'],
                        'EANSHOP':			partner['shop_iln'],
                        'CUSTOMERNUMBER':   partner['customernumber'],	
                        'DELDATESHOP':      datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
                        'TYPEOFPACKAGES':   product['packagetype'],
                    })
			
			# Mark sale.order ready for invoice
            order_marked = sock.execute(dbname, uid, pwd, 'sale.order', 'write', order_ids, {'ica_status': 'd',})
            dspadv_delivered = sock.execute(dbname, uid, pwd, 'ica.dspadv', 'create', {'mrpjournal_id': mrpjournal_ids[0], 'saleorder_id': order_record['id'],'status': 'c','blob': json.dumps(dspadv)})
    else:
        print "Nothing to dspadv\n"

    if not options.noupdate:
        mrpjournal_marked = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'write', mrpjournal_ids, {'saleorder_dspadv': today.strftime('%Y-%m-%d %H:%M')})
                
