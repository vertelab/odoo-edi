
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
# 2010-10-04 anders.wallenquist@vertel.se Fakturera 3 dagar gamla ordrar 

import wizard
import pooler
import os
import json
import netsvc
import datetime
from osv import fields, osv
from tools.translate import _


class ica_mrpjournal_do_invoice(wizard.interface):
    def _do_invoice(self, cr, uid, data, context):
        
        logger = netsvc.Logger()
        
        journal_cr = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        
        
        for jid in data['ids']:  # Om det är flera markerade dagjournaler

            journal_cr.write(cr, uid, [jid], {'status': 'f'})

            journal = journal_cr.read(cr,uid,jid)
            if journal['saleorder_invoice'] > 0:
                return {}
                
            product_cr =  pooler.get_pool(cr.dbname).get('product.product')
            partner_cr = pooler.get_pool(cr.dbname).get('res.partner')
            account_invoice_cr = pooler.get_pool(cr.dbname).get('account.invoice')
            line_cr = pooler.get_pool(cr.dbname).get('account.invoice.line')
            invoice_cr = pooler.get_pool(cr.dbname).get('ica.invoice')
            order_cr = pooler.get_pool(cr.dbname).get('sale.order')
            tax_cr = pooler.get_pool(cr.dbname).get('account.invoice.tax')


            today = datetime.datetime.today()

            logger.notifyChannel("warning", netsvc.LOG_CRITICAL,
                    "Invoices to work with '%s'  ." % account_invoice_cr.search(cr, uid, [("ica_mrpjournal",">",0),("state","=","open")]))



    # We need un invoiced 
            for invoice_record in account_invoice_cr.read(cr,uid,account_invoice_cr.search(cr, uid, [("ica_mrpjournal",">",0),("state","=","open")])):
                print invoice_record
       
                tot_discount = 0
                # There is already a ica.invoice
                if invoice_record['ica_invoice_id']:
                    print "ica.invoice already created %s" % invoice_record['ica_invoice_id']
                    continue
                    
                # sale.order
                order_record = order_cr.read(cr, uid,  order_cr.search(cr,uid, [("name","=", invoice_record['origin'])])) 
                if not order_record:
                    print "no order origin %s found (%s)" % (invoice_record['origin'], invoice_record['name'])
                    continue
                
                # Partner
                partner = partner_cr.read(cr, uid, order_record[0]['partner_id'][0])
     
                invoice = {
                    'HEA': {                
                        'MESSAGETYPE':      'invoice',
                        'LIN': [],
                    }
                }

                lin = {}  # Sortera på artikel
                for line in line_cr.read(cr,uid, line_cr.search(cr,uid,[('invoice_id','=',invoice_record['id'])])):
                    product = product_cr.read(cr, uid, line['product_id'][0])
                    pid = product['id']
                    tot_discount += line['discount']
                    if pid in lin:  # Accumulate orderlines with same product
                        lin[pid]['QTY_INVOICED'] +=  line['quantity']
                        lin[pid]['LINE_NET']     +=  line['price_subtotal']
                        lin[pid]['LIN_DISCOUNT'] +=  line['discount']
                    else:
                        lin[pid] = {
                                'EAN':              product['ean14'],
                                'SU_ARTICLECODE':   product['su_articlecode'],
                                'LISTPRICE':        line['price_unit'],
                                'TAXPERCENTAGE':    0,
                                'LIN_CHARGE':       0,
                                'QTY_INVOICED':     line['quantity'],
                                'LINE_NET':         line['price_subtotal'],
                                'LIN_DISCOUNT':     line['discount'],
                            }

                number = 10
                for pid in lin:
                    invoice['HEA']['LIN'].append({
                            'NUMBER':           number,
                            'EAN':              lin[pid]['EAN'],
                            'SU_ARTICLECODE':   lin[pid]['SU_ARTICLECODE'],
                            'QTY_INVOICED':     "%d" % lin[pid]['QTY_INVOICED'], 
                            'LINE_NET':         "%.2f" % lin[pid]['LINE_NET'],  
                            'LISTPRICE':        "%.2f" % lin[pid]['LISTPRICE'], 
                            'TAXPERCENTAGE':    "%.2f" % lin[pid]['TAXPERCENTAGE'],
                            'LIN_CHARGE':       "%.2f" % lin[pid]['LIN_CHARGE'],    
                            'LIN_DISCOUNT':     "%.2f" % lin[pid]['LIN_DISCOUNT'],  
                        })
                    number += 10

                invoice_tax_records = tax_cr.read(cr, uid, tax_cr.search(cr, uid, [("invoice_id","=",invoice_record['id'])]))  # A list of tax-rows from OpenERP

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
                invoice['HEA']['DELDATE']       =datetime.datetime.strptime(order_record[0]['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')  
                invoice['HEA']['EANBUYER']      =order_record[0]['eanbuyer']
                invoice['HEA']['EANSUPPLIER']   =order_record[0]['eansupplier']
                invoice['HEA']['SUPPLIER_ORGID']='556208-4698'
                invoice['HEA']['SUPPLIER_VATNR']='SE556208469801'
                invoice['HEA']['EANCONSIGNEE']  =order_record[0]['eanconsignee']
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

                ica_invoice_id = invoice_cr.create(cr, uid,  {'status': 'c', 'mrpjournal_id': jid, 'saleorder_id': order_record[0]['id'], 'blob': json.dumps(invoice)})         
                invoice_res = account_invoice_cr.write(cr, uid, invoice_record['id'], {'ica_invoice_id': ica_invoice_id})

            journal_cr.write(cr, uid, [jid], {'saleorder_invoice': today.strftime('%Y-%m-%d %H:%M')})  # mark journal done        
  
        return {'type': 'state','state':'end'}

    states = {
            'init' : {
                'actions' : [_do_invoice],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_invoice("ica.do_invoice")


class ica_mrpjournal_do_create_invoice(wizard.interface):
    def _do_create_invoice(self, cr, uid, data, context):
        logger = netsvc.Logger()
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        invoice_cr = pooler.get_pool(cr.dbname).get('account.invoice')

        # One invoice per supplier
        #order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),('EANSUPPLIER','LIKE','7350031550009')]), True)
        #order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),('EANSUPPLIER','LIKE','7300009025411')]), True)

        #3days = datetime.timedelta(days=3)

        today = datetime.datetime.today()
        threedays = today - datetime.timedelta(days=3)

        # Journals three days old not invoiced
        journals = journal.search(cr,uid,[("saleorder_invoice","=",False),("datum","<=",threedays.strftime("%Y-%m-%d"))])
        logger.notifyChannel("Info", netsvc.LOG_INFO,"Journals to invoice '%s' %s ." % (journals,threedays.strftime("%Y-%m-%d")))
        
        for journal_id in journals:
            logger.notifyChannel("warning", netsvc.LOG_WARNING,"Invoice journal_id '%s'  ." % journal_id)    
            inv_id = order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",journal_id),('eansupplier','=','7350031550009')]), True)
            invoice_cr.write(cr,uid, inv_id, {'ica_mrpjournal': journal_id}) # Mark invoice with journal
            inv_id = order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",journal_id),('eansupplier','=','7300009025411')]), True)
            invoice_cr.write(cr,uid, inv_id, {'ica_mrpjournal': journal_id}) # Mark invoice with journal

        return {}

    states = {
            'init' : {
                'actions' : [_do_create_invoice],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_create_invoice("ica.do_create_invoice")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
