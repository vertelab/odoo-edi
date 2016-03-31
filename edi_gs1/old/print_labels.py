#!/usr/bin/python

import xmlrpclib
import datetime
import json
import os
import string

from optparse import OptionParser

#parser = OptionParser(xusage="%prog --database=DBNAME --username=USER --password=PWD --server=SERVERNAME")
parser = OptionParser()
parser.add_option("-d", "--database", dest="dbname",help="use database DATABASE")
parser.set_defaults(dbname='test_aw11')
parser.add_option("-u", "--username", dest="username",help="use user USERNAME", default="admin")
parser.set_defaults(username='admin')
parser.add_option("-p", "--password", dest="pwd",help="use password PASSWORD", default="admin")
parser.set_defaults(pwd='admin')
parser.add_option("-s", "--server", dest="servername",help="use server http://servername:port%s ")
parser.set_defaults(servername='http://localhost:8069%s')
parser.add_option("-m", "--mrpid", dest="mrpid",help="use mrpid MRPID")
parser.set_defaults(mrpid='119')
parser.add_option("-D", "--depa", dest="depa",help="use depa DEPA_ID")
parser.set_defaults(depa='1704')
parser.add_option("-L", "--label", dest="label",help="use label LABEL_ID")
parser.set_defaults(label='1')
parser.add_option("-u", "--ugrp", dest="ugrp",help="use ugrp UTSKRIFTSGRUPP")
parser.set_defaults(ugrp='1')

parser.add_option("-i", "--mappid", dest="id",help="use id ID")
parser.set_defaults(id='0')
(options, args) = parser.parse_args()


#username = 'admin'  # username and password will change in the future
pwd = options.pwd
dbname = options.dbname  # This is the test-database for now
#servername = "http://erp.greenvision.nu:8069%s"
#servername = "http://localhost:8069%s"

#  Open ERP listens at port 8069
sock_common = xmlrpclib.ServerProxy (options.servername % "/xmlrpc/common")
uid = sock_common.login(options.dbname, options.username, options.pwd)
sock = xmlrpclib.ServerProxy(options.servername % "/xmlrpc/object", use_datetime=True)

today = datetime.datetime.today()

def partner_adr(EAN):
    partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', sock.execute(dbname, uid, pwd, 'res.partner', 'search',[("Shop_iln","=",EAN)]))

    if not partner:
        return EAN

    addr =  {}
    for addr_rec in sock.execute(dbname, uid, pwd, 'res.partner.address', 'read', partner[0]['address'] ):
        addr[addr_rec['type']] = addr_rec

    adress = addr.get('delivery',addr.get('default',{'street': 'Street','zip':'Zip','city':'City'}))
    for i in ['street','zip','city']:
        if not adress[i]:
            adress[i]=''
    
    return unicode('"' + partner[0]['name'] + '\\n' + adress['street'] + '\\n' + adress['zip'] + ' ' + adress['city'] + '"')


no=1

# Just a search to check invoice_ids is growing
#dspadv_ids = sock.execute(dbname, uid, pwd, 'ica.dspadv', 'search',[("mrpjournal_id","=",options.mrpid)])  
#sscc_ids = sock.execute(dbname, uid, pwd, 'ica.sscc', 'search',[])  
label_ids = sock.execute(dbname, uid, pwd, 'ica.label', 'search',[("ica_mrpjournal","=",options.mrpid)])  
#dspadv_ids = sock.execute(dbname, uid, pwd, 'ica.dspadv', 'search',[])
#print sscc_ids, options.mrpid



if label_ids:
    for label_id in label_ids:
        label = sock.execute(dbname, uid, pwd, 'ica.label', 'read', label_id)
        product = sock.execute(dbname, uid, pwd, 'product.product', 'read', label['product_id'][0])
        utlevvecka = datetime.datetime.strptime(label['deldateshop'],'%Y-%m-%d').strftime('%W')
        utlevdag = datetime.datetime.strptime(label['deldateshop'],'%Y-%m-%d').strftime('%w')
        if utlevdag == '0':
            utlevdag = '7'
        

        txt = partner_adr(label['eansender']).encode('utf-8')+","										# 00
        txt +=partner_adr(label['eanreceiver']).encode('utf-8')+','										# 01
        txt +=product['su_articlecode'].encode('utf-8')+','												# 02
        txt +=product['name'].encode('utf-8')+','														# 03
        txt +="%09d" % label_id+','																		# 04
        txt +=label['plockid']+','																		# 05
        
        txt +=label['customernumber'].encode('utf-8')+','												# 06
        txt +=label['bundle_qty']+','																	# 07
        txt +="%02d %s" % (int(utlevvecka),utlevdag)                                    				# 08
        txt +="%03d/%02d" % (int(label['lass']),int(label['pl']))+','									# 09
        txt +="%02d/%02d" % (int(label['utlevomr']),int(label['port']))+','								# 10
        txt +="%03d-%03d" % (int(label['ruta1']),int(label['ruta2']))+','								# 11
        
        txt +=partner_adr(label['eanshop']).encode('utf-8')+','											# 12
		txt +=label['pallet_no']+','																	# 13
		txt +=label['typeofpackage']+','																# 14
        txt +=label['sscc'].encode('utf-8')+','															# 15
        txt +='[00]'+label['sscc'].encode('utf-8')+','													# 16
        txt +='/tmp/'+options.id+'/'+label['sscc'].encode('utf-8')+'.png' 								# 17	Package image
        print txt
        
        label_printed = sock.execute(dbname, uid, pwd, 'ica.label', 'write', label_id, {'date_printed': today, })

else:
    print "Nothing to label\n"
