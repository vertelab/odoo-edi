
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
import netsvc
import datetime
from osv import fields, osv
from tools.translate import _

def addPackage(ord_id,cr,uid):
    today = datetime.datetime.today()
    logger = netsvc.Logger()
    package_line = {}
    for line in pooler.get_pool(cr.dbname).get('sale.order.line').read(cr,uid,
                    pooler.get_pool(cr.dbname).get('sale.order.line').search(cr,uid,[("order_id","=",ord_id)])):    
        # Product
        product = pooler.get_pool(cr.dbname).get('product.product').read(cr, uid,line['product_id'][0])  
        logger.notifyChannel("Info", netsvc.LOG_INFO,
						"appPackage product '%s'   ." % (product['packaging'],))
        if product['packaging']:
            package = pooler.get_pool(cr.dbname).get('product.packaging').read(cr,uid, product['packaging'][0])

            logger.notifyChannel("INFO", netsvc.LOG_INFO,
						    "Package '%s'  ." % (package))
                       
            # Product_package Add package only if there is a product for the package
            product_package_id = pooler.get_pool(cr.dbname).get('product.product').search(cr, uid,[("default_code","=",package['ean'])])
            if package['ean'] <> '' and product_package_id:
                product_package = pooler.get_pool(cr.dbname).get('product.product').read(cr, uid,product_package_id)  
                logger.notifyChannel("INFO", netsvc.LOG_INFO,
						    "appPackage product_package '%s' '%s'." % (product_package[0],product_package_id))
                if not package_line.get(package['ean']):
                    package_line[package['ean']] = {
                        'delay':            0.0,
                        'discount':         0.0,
                        'invoiced':         0,
                        'name':             product_package[0]['name'],
                        'notes':            '',
                        'order_id':         ord_id,
                        'price_unit':       product_package[0]['list_price'],
                        'product_id':       product_package[0]['id'],
                        'product_packaging': 0,
                        'product_uom':      product_package[0]['uom_id'][0],
                        'product_uom_qty':  1,
                        'product_uos':      1,
                        'product_uos_qty':  1,
                        'sequence':         line['sequence'],
                        'state':            'confirmed',
                        'th_weight':        0,
                        'type':             'make_to_stock',
                        'tax_id':           product_package[0]['taxes_id'],
                    }
                else:
                    package_line[package['ean']]['product_uom_qty'] += 1

    for ean in package_line:
        logger.notifyChannel("INFO", netsvc.LOG_INFO,"Package_line '%s'  ." % (package_line[ean]))
        saleorderline_id = pooler.get_pool(cr.dbname).get('sale.order.line').create(cr, uid, {
            'delay':            0.0,
            'discount':         0.0,
            'invoiced':         0,
            'name':             package_line[ean]['name'],
            'notes':            '',
            'order_id':         ord_id,
            'price_unit':       package_line[ean]['price_unit'],
            'product_id':       package_line[ean]['product_id'],
            'product_packaging': 0,
            'product_uom':      package_line[ean]['product_uom'],
            'product_uom_qty':  1,
            'product_uos':      1,
            'product_uos_qty':  1,
            'sequence':         99,
            'state':            'confirmed',
            'th_weight':        0,
            'type':             'make_to_stock',
            'tax_id':           package_line[ean]['tax_id'],
        })
        for tax in package_line[ean]['tax_id']:
            cr.execute('INSERT INTO sale_order_tax ("order_line_id", "tax_id", "create_uid", "create_date") VALUES (' + str(saleorderline_id) + ',' + str(tax) + ', ' + str(uid) + ', ' + today.strftime("'%Y-%m-%d %H:%M'") + ' )')
 
    return


# DESADV
class ica_mrpjournal_do_dspadv(wizard.interface):
    today = datetime.datetime.today()

    def _do_dspadv(self, cr, uid, data, context):
        today = datetime.datetime.today()
        
        for jid in data['ids']:  # Om det är flera markerade dagjournaler

            journal_cr = pooler.get_pool(cr.dbname).get('ica.mrpjournal')
            journal_cr.write(cr, uid, [jid], {'status': 'l'})

            journal = journal_cr.read(cr,uid,jid)
            if journal['saleorder_dspadv'] > 0:
                raise osv.except_osv(_('Redan leveransbekräftad'), _('%s') % (journal['saleorder_dspadv']))
                return {}

            cr.execute("""select count(id) from ica_label where ica_mrpjournal = %d and completed = 1""" % (jid))
            kollin = cr.fetchone()[0]     
            if  kollin == 0:
                raise osv.except_osv(_('Inga kollin producerade'), _('%s kollin completed') % (kollin))
                return {}

            label_cr = pooler.get_pool(cr.dbname).get('ica.label')
            order_cr = pooler.get_pool(cr.dbname).get('sale.order')
            order_ids = order_cr.search(cr, uid, [("ica_mrpjournal","=",jid)])
            dspadv_cr = pooler.get_pool(cr.dbname).get('ica.dspadv')
            product_cr =  pooler.get_pool(cr.dbname).get('product.product')
            line_cr = pooler.get_pool(cr.dbname).get('sale.order.line')

            orders_done = False
            line_qty = {}

            if order_ids:
                print order_ids
                for order_record in order_cr.read(cr, uid, order_ids):
                    for label_record in label_cr.read(cr, uid, label_cr.search(cr, uid, [("order_id","=",order_record['id'])])):
                        if not orders_done:  # Create the HEA-record only once, we have to do it when we have an ica_label
                            orders_done = True
    #                    if not orders_done[order_record['id']]:
    #                       orders_done[order_record['id']] = True
                            netsvc.Logger().notifyChannel("do_dspadv", netsvc.LOG_INFO,"ica_label '%s' ESTDELDATE %s  ." % (label_record,datetime.datetime.strptime(label_record['estdeldate'],'%Y-%m-%d').strftime('%Y%m%d')))
                            dspadv = {
                                'HEA': {
                                    'MESSAGETYPE':      'desadv01',
                                    'EANSENDER':        label_record['eanreceiver'],
                                    'EANRECEIVER':      label_record['eansender'],
                                    'TEST':             '0',
                                    'DESADVNUMBER':     label_record['desadvnumber'],   
                                    'DESADVDATE':       datetime.datetime.strptime(label_record['date_order'],'%Y-%m-%d').strftime('%Y%m%d'),
                                    'ESTDELDATE':       datetime.datetime.strptime(label_record['estdeldate'],'%Y-%m-%d').strftime('%Y%m%d'),
                                    'EANBUYER':         label_record['eanbuyer'],
                                    'EANSHIPPER':       label_record['eansupplier'],    
                                    'EANDELIVERY':      label_record['eandelivery'],    
                                    'TRANSPORTNUMBER':  label_record['transportnumber'],
                                    'PAC': [],                
                                }
                            }

                        # Product
                        product = product_cr.read(cr, uid,label_record['product_id'][0])  
                        line_id = label_record['line_id'][0]
     
                        if label_record['completed'] == 1:

                            dspadv['HEA']['PAC'].append({
                                'PACNUMBER':        label_record['pacnumber'],
                                'SSCC':             label_record['sscc'],
                                'ORDERNUMBER':      label_record['ordernumber'],
                                'EANCONSIGNEE':     label_record['eanconsignee'],
                                'EANSHOP':          label_record['eanshop'],
                                'CUSTOMERNUMBER':   label_record['customernumber'], 
                                'DELDATESHOP':      datetime.datetime.strptime(label_record['deldateshop'],'%Y-%m-%d').strftime('%Y%m%d'),
                                'TYPEOFPACKAGES':   label_record['typeofpackage'],
                            })

                            if not line_id in line_qty:  # line_qty was > 1
                                line_qty[line_id] = 1
                            else:
                                line_qty[line_id] += 1   
                        else:
                            if not line_id in line_qty:  # line_qty was 1
                                line_qty[line_id] = 0
                            
                    # Mark sale.order ready for invoice
                    order_marked = order_cr.write(cr, uid,  order_ids, {'ica_status': 'd',})
                    dspadv_id = dspadv_cr.create(cr, uid,{'mrpjournal_id': jid, 'saleorder_id': order_record['id'],'status': 'c','blob': json.dumps(dspadv)})
                    label_cr.write(cr,uid, [label_record['id']],{'dspadv_id': dspadv_id})
                    orders_done = False
                # Update qty on order_lines
                for line_id in line_qty:
                    for line_record in line_cr.read(cr, uid, line_id):
                        line_cr.write(cr, uid, [line_id], {'product_uom_qty': line_qty[line_id]})  
                         
                for ord_id in order_ids:  # Add packaging as order-lines
                    addPackage(ord_id,cr,uid)
          
            journal_cr.write(cr, uid, [jid], {'saleorder_dspadv': today.strftime('%Y-%m-%d %H:%M')})  # mark journal done        


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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
