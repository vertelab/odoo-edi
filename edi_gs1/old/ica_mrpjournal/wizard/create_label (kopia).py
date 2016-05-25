
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

class ica_label_create(wizard.interface):
    today = datetime.datetime.today()

    def _create(self, cr, uid, data, context):
        today = datetime.datetime.today()
        logger = netsvc.Logger()
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
        package_cr = pooler.get_pool(cr.dbname).get('product.package')

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
                    package = package_cr.read(cr,uid, product['packaging'][0])
                        
                    typeofpackage = package['ul'][0]

                    logger.notifyChannel("Critical", netsvc.LOG_CRITICAL,
                        "Packages '%s' '%s'  ." % (product['packaging'],package['ul']))

 
                    q=1
                    while q<=line['product_uom_qty']:
                        q+=1
                        edi_record = edi_cr.read(cr, uid, 1, ['next_sscc'])
                        if not edi_record['next_sscc']:
                            edi_record['next_sscc']=1
                            res = edi_cr.create(cr, uid, {'next_sscc': edi_record['next_sscc']})
                        res = edi_cr.write(cr, uid, 1, {'next_sscc': edi_record['next_sscc']+1})

                        pallet_no = edi_record['next_sscc']
                        sscc = makeSSCC(edi_record['next_sscc'])
                        sscc_id = sscc_cr.create(cr, uid, {
                            'sscc':             sscc,
                            'line_id':          line['id'],
                            'EANSENDER':        order_record['eanreceiver'],
                            'EANRECEIVER':      order_record['eansender'],
                            'EANSHOP':          partner['shop_iln'],
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
                                'desadvnumber':     order_record['name'],   
                                'dpsadv_id':        0,
                                'eanbuyer':         order_record['eanbuyer'],
                                'eanconsignee':     order_record['eanconsignee'],
                                'eandelivery':      order_record['eandelivery'],
                                'eanreceiver':      order_record['eanreceiver'],
                                'eansender':        order_record['eansender'],
                                'eansupplier':      order_record['eansupplier'],    
                                'eanshop':          order_record['eanshop'],
                                'etsdeldate':       datetime.datetime.strptime(order_record['date_promised'],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d'),
                                'ica_mrpjournal':   order_record['ica_mrpjournal'],                            
                                'line_id':          line['id'],
                                'order_id':         order_record['id'],
                                'ordernumber':      order_record['origin'],
                                'pacnumber':        pacnumber,
                                'partner_id':       partner['id'],
                                'product_id':       product['id'],
                                'sscc':             sscc,
                                'transportnumber':  edi_record['next_desadv'],
                                'typeofpackage':    typeofpackage,
                                'utskriftsgrupp':   product['utskriftsgrupp'],
                                'utskriftsprio':    product['utskriftsprio'],
                                'plockid':          product['loc_rack'],
                                'pallet_no':        pallet_no,
                                                                
                                'utlevomr':         order_record['utlevomr'],
                                'port':             order_record['port'],
                                'lass':             order_record['lass'],
                                'pl':               order_record['pl'],
                                'ruta1':            order_record['ruta1'],
                                'ruta2':            order_record['ruta2'],
                                
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
