
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

import wizard
import pooler
import os
import json
import datetime
from osv import fields, osv
from tools.translate import _


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




class ica_mrpjournal_print_labels(wizard.interface):

    def _printLabels(self, cr, uid, data, context):
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        print data['id'], cr.dbname
        print 'print_label -m %d -d %s' % (data['id'],cr.dbname)
        os.system('print_label -m %d -d %s' % (data['id'],cr.dbname))
        return {}

    states = {
            'init' : {
                'actions' : [_printLabels],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_print_labels("ica.mrpprint_labels")

class ica_mrpjournal_do_import_order_edi(wizard.interface):

    def _do_import_order(self, cr, uid, data, context):
        # We dont have any journal yet (probably)
        os.system('/usr/share/greenvision/do_import_order.py --database=%s' % cr.dbname)
#        'status': fields.selection((('i','EDI order'), ('s',"Kundorder"), ('o','Orderbekräftelse'), ('l','Leveransbekräftelse'), ('f','Faktura')), 'Status', size=10,),
        return {}

    states = {
            'init' : {
                'actions' : [_do_import_order],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_import_order_edi("ica.do_import_order_edi")

class ica_mrpjournal_do_import_order_sale(wizard.interface):
    def _do_import_order(self, cr, uid, data, context):
        today = datetime.datetime.today()
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        journal.write(cr, uid, [data['id']], {'status': 's'})
        cr.commit()
        os.system('/usr/share/greenvision/do_create_saleorder.py --journal=%d --database=%s --noupdate=1' % (data['id'],cr.dbname))
        journal.write(cr, uid, [data['id']], {'saleorder_imported': today.strftime('%Y-%m-%d %H:%M')})  # mark journal done
        cr.commit()
        return {}

    states = {
            'init' : {
                'actions' : [_do_import_order],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_import_order_sale("ica.do_import_order_sale")


class ica_mrpjournal_do_ordrsp(wizard.interface):
    def _do_ordrsp(self, cr, uid, data, context):
        today = datetime.datetime.today()
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        journal.write(cr, uid, [data['id']], {'status': 'o'})
        cr.commit()
        os.system('/usr/share/greenvision/do_ordrsp.py --journal=%d --database=%s --noupdate=1' % (data['id'],cr.dbname))
        journal.write(cr, uid, [data['id']], {'saleorder_ordrsp': today.strftime('%Y-%m-%d %H:%M')})  # mark journal done
        return {}

    states = {
            'init' : {
                'actions' : [_do_ordrsp],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_ordrsp("ica.do_ordrsp")

# DESADV
class ica_mrpjournal_do_dspadv(wizard.interface):
    today = datetime.datetime.today()

    def _do_dspadv(self, cr, uid, data, context):
        today = datetime.datetime.today()
        journal_cr = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        journal_cr.write(cr, uid, [data['id']], {'status': 'l'})

        journal = journal_cr.read(cr,uid,data['id'])
        if journal['saleorder_dspadv'] > 0:
            return {}

        label_cr = pooler.get_pool(cr.dbname).get('ica.label')
        order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        order_ids = order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id'])])
        dspadv_cr = pooler.get_pool(cr.dbname).get('ica.dspadv')
        
        orders_done = []
        line_qty = []

        if order_ids:
            print order_ids
            for order_record in order_cr.read(cr, uid, order_ids):
                for label_record in label_cr.read(cr, uid, label_cr.search(cr, uid, [("order_id","=",order_record['id']),('completed',"=",False),('dspadv_id','=',0)])):

                    if not orders_done[order_record['id']]:
                        orders_done[order_record['id']] = True
                        dspadv = {
                            'HEA': {
                                'MESSAGETYPE':      'desadv01',
                                'EANSENDER':        label_record['eanreceiver'],
                                'EANRECEIVER':      label_record['eansender'],
                                'TEST':             '0',
                                'DESADVNUMBER':		label_record['name'],	
                                'DESADVDATE':	    label_record['desadvdate'],
                                'ESTDELDATE':	    label_record['estdeldate'],
                                'EANBUYER':	        label_record['eanbuyer'],
                                'EANSHIPPER':	    label_record['eansupplier'],    
                                'EANDELIVERY':	    label_record['eandelivery'],	
                                'TRANSPORTNUMBER':  label_record['transportnumber'],
                                'PAC': [],                
                            }
                        }

                    # Product
                    product = product_cr.read(cr, uid,line['product_id'][0])  
 

                dspadv['HEA']['PAC'].append({
                    'PACNUMBER':        label_record['pacnumber'],
                    'SSCC':				label_record['sscc'],
                    'ORDERNUMBER':		label_record['ordernumber'],
                    'EANCONSIGNEE':     label_record['eanconsignee'],
                    'EANSHOP':			label_record['eanshop'],
                    'CUSTOMERNUMBER':   label_record['customernumber'],	
                    'DELDATESHOP':      label_record['deldateshop'],
                    'TYPEOFPACKAGES':   label_record['typeofpackage'],
                })

                line_qty[label_record['line_id']] += 1
                
                # Mark sale.order ready for invoice
                order_marked = order_cr.write(cr, uid,  order_ids, {'ica_status': 'd',})
                dspadv_id = dspadv_cr.create(cr, uid,{'mrpjournal_id': data['id'], 'saleorder_id': order_record['id'],'status': 'c','blob': json.dumps(dspadv)})
                label_cr.write(cr,uid, [label_record['id']],{'dspadv_id': dspadv_id})
            # Update qty on order_lines
            for line_id in line_qty:
                for line_record in line_cr.read(cr, uid, line_id):
                    line_cr.write(cr, uid, [line_id], {'qty': line_qty[line_id]})  
                            
        journal_cr.write(cr, uid, [data['id']], {'saleorder_dspadv': today.strftime('%Y-%m-%d %H:%M')})  # mark journal done        
        return {}

    states = {
            'init' : {
                'actions' : [_do_dspadv],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_mrpjournal_do_dspadv("ica.do_dspadv")


class ica_mrpjournal_do_invoice(wizard.interface):
    def _do_invoice(self, cr, uid, data, context):
        journal_cr = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        journal_cr.write(cr, uid, [data['id']], {'status': 'f'})

        journal = journal_cr.read(cr,uid,data['id'])
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

        for invoice_record in account_invoice_cr.read(cr,uid,account_invoice_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),("state","=","open")])):
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
                    'MESSAGETYPE':		'invoice',
                    'LIN': [],
                }
            }

            lin = {}
            for line in line_cr.read(cr,uid, line_cr.search(cr,uid,[('invoice_id','=',invoice_record['id'])])):
                product = product_cr.read(cr, uid, line['product_id'][0])
                pid = product['id']
                tot_discount += line['discount']
                if pid in lin:
                    lin[pid]['QTY_INVOICED'] +=	 line['quantity']
                    lin[pid]['LINE_NET']     +=  line['price_subtotal']
                    lin[pid]['LIN_DISCOUNT'] +=  line['discount']
                else:
                    lin[pid] = {
                            'EAN':              product['ean14'],
                            'SU_ARTICLECODE':	product['su_articlecode'],
                            'LISTPRICE': 		line['price_unit'],
                            'TAXPERCENTAGE': 	0,
                            'LIN_CHARGE': 		0,
                            'QTY_INVOICED':     line['quantity'],
                            'LINE_NET':         line['price_subtotal'],
                            'LIN_DISCOUNT':     line['discount'],
                        }

            number = 10
            for pid in lin:
                invoice['HEA']['LIN'].append({
                        'NUMBER':           number,
                        'EAN':              lin[pid]['EAN'],
                        'SU_ARTICLECODE':	lin[pid]['SU_ARTICLECODE'],
                        'QTY_INVOICED':	    "%d" % lin[pid]['QTY_INVOICED'], 
                        'LINE_NET':         "%.2f" % lin[pid]['LINE_NET'],	
                        'LISTPRICE': 		"%.2f" % lin[pid]['LISTPRICE'],	
                        'TAXPERCENTAGE': 	"%.2f" % lin[pid]['TAXPERCENTAGE'],
                        'LIN_CHARGE': 		"%.2f" % lin[pid]['LIN_CHARGE'],	
                        'LIN_DISCOUNT': 	"%.2f" % lin[pid]['LIN_DISCOUNT'],	
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

            ica_invoice_id = invoice_cr.create(cr, uid,  {'status': 'c', 'mrpjournal_id': data['id'], 'saleorder_id': order_record[0]['id'], 'blob': json.dumps(invoice)})         
            invoice_res = account_invoice_cr.write(cr, uid, invoice_record['id'], {'ica_invoice_id': ica_invoice_id})

        journal_cr.write(cr, uid, [data['id']], {'saleorder_invoice': today.strftime('%Y-%m-%d %H:%M')})  # mark journal done        
  
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
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        invoice_cr = pooler.get_pool(cr.dbname).get('account.invoice')

        # One invoice per supplier
        #order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),('EANSUPPLIER','LIKE','7350031550009')]), True)
        #order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),('EANSUPPLIER','LIKE','7300009025411')]), True)
        inv_id = order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),('eansupplier','=','7350031550009')]), True)
        invoice_cr.write(cr,uid, inv_id, {'ica_mrpjournal': data['id']}) # Mark invoice with journal
        inv_id = order_cr.action_invoice_create(cr, uid, order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id']),('eansupplier','=','7300009025411')]), True)
        invoice_cr.write(cr,uid, inv_id, {'ica_mrpjournal': data['id']}) # Mark invoice with journal

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

class ica_label_create(wizard.interface):
    today = datetime.datetime.today()

    def _create(self, cr, uid, data, context):
        today = datetime.datetime.today()
        journal_cr = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        journal_cr.write(cr, uid, [data['id']], {'status': 'l'})

        journal = journal_cr.read(cr,uid,data['id'])
        if journal['saleorder_dspadv'] > 0:
            return {}

        order_cr = pooler.get_pool(cr.dbname).get('sale.order')
        order_ids = order_cr.search(cr, uid, [("ica_mrpjournal","=",data['id'])])

        product_cr =  pooler.get_pool(cr.dbname).get('product.product')
        partner_cr = pooler.get_pool(cr.dbname).get('res.partner')
        line_cr = pooler.get_pool(cr.dbname).get('sale.order.line')
        edi_cr = pooler.get_pool(cr.dbname).get('ica.edi')
        sscc_cr = pooler.get_pool(cr.dbname).get('ica.sscc')
        label_cr = pooler.get_pool(cr.dbname).get('ica.label')

        if order_ids:
            for order_record in order_cr.read(cr, uid, order_ids):
                # Partner
                partner = partner_cr.read(cr, uid, order_record['partner_id'][0])

                transportnumber = 0

                pacnumber = 0
                # One PAC for each sale.order.line and each product_oum_qty
                for line in line_cr.read(cr, uid, line_cr.search(cr, uid, [("order_id","=",order_record['id'])])):
                    # Product
                    product = product_cr.read(cr, uid,line['product_id'][0])  
 
                    q=1
                    while q<=line['product_uom_qty']:
                        q+=1
                        edi_record = edi_cr.read(cr, uid, 1, ['next_sscc'])
                        if not edi_record['next_sscc']:
                            edi_record['next_sscc']=1
                            res = edi_cr.create(cr, uid, {'next_sscc': edi_record['next_sscc']})
                        res = edi_cr.write(cr, uid, 1, {'next_sscc': edi_record['next_sscc']+1})

                        sscc = makeSSCC(edi_record['next_sscc'])
                        sscc_id = sscc_cr.create(cr, uid, {
                            'sscc':             sscc,
                            'line_id':          line['id'],
                            'EANSENDER':        order_record['eanreceiver'],
                            'EANRECEIVER':      order_record['eansender'],
                            'EANSHOP':			partner['shop_iln'],
                            'CUSTOMERNUMBER':   partner['customernumber'],	
                            'DELDATESHOP':      datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
                            'product_id':       product['id'],
                            'ica_mrpjournal':   order_record['ica_mrpjournal'],
                            })

                        pacnumber += 1
                        label = label_cr.create(cr, uid, {
                                'completed':        False,
                                'customernumber':   partner['customernumber'],	
                                'date_order':       datetime.datetime.strptime(order_record['date_order'],'%Y-%m-%d').strftime("%Y%m%d"),
                                'deldateshop':      datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
                                'desadvnumber':		order_record['name'],	
                                'dpsadv_id':        0,
                                'eanbuyer':	        order_record['eanbuyer'],
                                'eanconsignee':     order_record['eanconsignee'],
                                'eandelivery':	    order_record['eandelivery'],
                                'eanreceiver':      order_record['eanreceiver'],
                                'eansender':        order_record['eansender'],
                                'eansupplier':	    order_record['eansupplier'],    
                                'eanshop':			order_record['eanshop'],
                                'etsdeldate':	    datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
                                'ica_mrpjournal':   order_record['ica_mrpjournal'],                            
                                'line_id':          line['id'],
                                'order_id':         order_record['id'],
                                'ordernumber':		order_record['origin'],
                                'pacnumber':        pacnumber,
                                'partner_id':       partner['id'],
                                'product_id':       product['id'],
                                'sscc':             sscc,
                                'transportnumber':  edi_record['next_desadv'],
                                'typeofpackage':    product['packagetype'],
                            })                

        return {}

    states = {
            'init' : {
                'actions' : [_create],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_label_create("ica.label_create")

class ica_label_print(wizard.interface):

    def _printLabels(self, cr, uid, data, context):
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
        print data['id'], cr.dbname
        print 'print_label -m %d -d %s' % (data['id'],cr.dbname)
        os.system('print_label -m %d -d %s' % (data['id'],cr.dbname))
        return {}

    states = {
            'init' : {
                'actions' : [_printLabels],
                'result'  : {
                        'type' : 'state',
                        'state' : 'end'}
                },
        }
ica_label_print("ica.label_print")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
