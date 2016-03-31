#!/usr/bin/python

# Create INVOICE from account.invoice

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
uid = sock_common.login(options.dbname, options.username, options.pwd)
sock = xmlrpclib.ServerProxy(options.servername % "/xmlrpc/object", use_datetime=True)



today = datetime.datetime.today()

for invoice_record in sock.execute(dbname, uid, pwd, 'account.invoice', 'read', sock.execute(dbname, uid, pwd, 'account.invoice', 'search',[("state","=", 'open')])): # state = draft create ica.invoice, set state = done

    tot_discount = 0

    # There is already a ica.invoice
    if invoice_record['ica_invoice_id']:
        print "ica.invoice already created %s" % invoice_record['ica_invoice_id']
        continue
        
    # sale.order
    order_record = sock.execute(dbname, uid, pwd, 'sale.order', 'read', sock.execute(dbname, uid, pwd, 'sale.order', 'search',[("name","=", invoice_record['origin'])])) 
    if not order_record:
        print "no order origin %s found (%s)" % (invoice_record['origin'], invoice_record['name'])
        continue
        
    # Mrp journal
    mrpjournal = sock.execute(dbname, uid, pwd, 'ica.mrpjournal', 'read', order_record[0]['ica_mrpjournal'])
    if not mrpjournal:
        print "order not connected to mrp journal ",order_record[0]['ica_mrpjournal']
        continue

#  Is it nessesery to check this status, we already know there is an invoice so they have started? 
#    if not mrpjournal['status'] == 'f':
#        continue
    
    # Partner
    partner = sock.execute(dbname, uid, pwd, 'res.partner', 'read', order_record[0]['partner_id'][0])
    if not partner['property_payment_term']:
        partner['property_payment_term'] = []    
        partner['property_payment_term'].append(1) # check this

    account = sock.execute(dbname, uid, pwd, 'account.account', 'read', sock.execute(dbname, uid, pwd, 'account.account', 'search', [('code','=',"1102")]))

    edi_record = sock.execute(dbname, uid, pwd, 'ica.edi', 'read', 1, ['next_invoicenbr'])
    if not edi_record['next_invoicenbr']:
        edi_record['next_invoicenbr']=1
        res = sock.execute(dbname, uid, pwd, 'ica.edi', 'create', {'next_invoicenbr': edi_record['next_invoicenbr']})
    res = sock.execute(dbname, uid, pwd, 'ica.edi', 'write', 1, {'next_invoicenbr': edi_record['next_invoicenbr']+1})

    addr =  {}
    for addr_rec in sock.execute(dbname, uid, pwd, 'res.partner.address', 'read', partner['address']):
        addr[addr_rec['type']] = addr_rec

    invoice = {
        'HEA': {                
            'MESSAGETYPE':		'invoice',
            'LIN': [],
        }
    }

    for line in sock.execute(dbname, uid, pwd, 'sale.order.line', 'read', sock.execute(dbname,uid,pwd, 'sale.order.line','search',[('order_id','=',order_record[0]['id'])])):

        product = sock.execute(dbname, uid, pwd, 'product.product', 'read', line['product_id'][0])

        su_articlecode = product.get('su_articlecode','1234567')
        if not su_articlecode:
                su_articlecode = "123456"

        tot_discount += line['discount']
            
        print line
        invoice['HEA']['LIN'].append({
                'NUMBER':           line['sequence'],
                'EAN':              product['ean14'],
                'SU_ARTICLECODE':	su_articlecode,
                'QTY_INVOICED':	    "%d" % line['product_uom_qty'], 
                'LINE_NET':         "%.2f" % line['price_subtotal'],	
                'LISTPRICE': 		"%.2f" % line['price_net'],	
                'TAXPERCENTAGE': 	'', 	
                'LIN_CHARGE': 		'',	
                'LIN_DISCOUNT': 	line['discount'],	
            })

    invoice_tax_records = sock.execute(dbname, uid, pwd, 'account.invoice.tax', 'read', sock.execute(dbname, uid, pwd, 'account.invoice.tax', 'search',[("invoice_id","=",invoice_record['id'])]))  # A list of tax-rows from OpenERP

    taxamount1 = 0
    taxamount2 = 0
    taxamount3 = 0
# Check constants for tax_code_id / name
    for tax in invoice_tax_records:
        if tax['name'] == 'Moms 25%':
            taxamount1 += tax['tax_amount']
        if tax['name'] == 'Moms 12%':
            taxamount2 += tax['tax_amount']
        if tax['name'] == 'Moms 6%':
            taxamount2 += tax['tax_amount']

    if not invoice_record['date_due']:
        invoice_record['date_due']='2010-01-01'
    date_due = datetime.datetime.strptime(invoice_record['date_due'],'%Y-%m-%d').strftime('%Y%m%d')

    invoice['HEA']['MESSAGETYPE']   ='invoice'
    invoice['HEA']['EANRECEIVER']   =order_record[0]['eansender']
    invoice['HEA']['EANSENDER']     =order_record[0]['eanreceiver']
    invoice['HEA']['TEST']          ='0'
    invoice['HEA']['INVOICENUMBER'] =invoice_record['number']
    invoice['HEA']['INVOICEDATE']   =datetime.datetime.strptime(invoice_record['date_invoice'],'%Y-%m-%d').strftime('%Y%m%d')
    invoice['HEA']['DELDATE']       =datetime.datetime.strptime(mrpjournal['saleorder_dspadv'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')
    invoice['HEA']['EANBUYER']      =order_record[0]['eanbuyer']
    invoice['HEA']['EANSUPPLIER']   =order_record[0]['eansupplier']
    invoice['HEA']['SUPPLIER_ORGID']='556208-4698'
    invoice['HEA']['SUPPLIER_VATNR']='SE556208469801'
    invoice['HEA']['EANCONSIGNEE']  =partner['consignee_iln']
    invoice['HEA']['TOT_CHARGE']    ="%.2f" % invoice_record['amount_total']
    invoice['HEA']['TOT_DISCOUNT']  ="%.2f" % tot_discount
    invoice['HEA']['DISTRIBUTION']= 'ICA'
    invoice['HEA']['LASTDATECASHDISC']=''
    invoice['HEA']['DUEDATE']       =date_due
    invoice['HEA']['TOTALINVOIC']   ="%.2f" % invoice_record['amount_total']
    invoice['HEA']['TOTALLINE_NET'] ="%.2f" % invoice_record['amount_untaxed']
    invoice['HEA']['TOTALTAXABLE']  ="%.2f" % invoice_record['amount_untaxed']
    invoice['HEA']['TOTALTAX']      ="%.2f" % invoice_record['amount_tax']
    invoice['HEA']['SUBJECTPAYDISC']=''
    invoice['HEA']['TAXPERCENTAGE1']='25.0'
    invoice['HEA']['TAXAMOUNT1']    ="%.2f" % taxamount1
    invoice['HEA']['TAXPERCENTAGE2']='12.0'
    invoice['HEA']['TAXAMOUNT2']    ="%.2f" % taxamount2
    invoice['HEA']['TAXPERCENTAGE3']='6.0'
    invoice['HEA']['TAXAMOUNT3']    ="%.2f" % taxamount3

    ica_invoice_id = sock.execute(dbname, uid, pwd, 'ica.invoice', 'create', {'status': 'c', 'mrpjournal_id': mrpjournal['id'], 'saleorder_id': order_record[0]['id'], 'blob': json.dumps(invoice)})         
    invoice_res = sock.execute(dbname, uid, pwd, 'account.invoice', 'write', invoice_record['id'], {'ica_invoice_id': ica_invoice_id})
