
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
import netsvc
import subprocess
from osv import fields, osv
from tools.translate import _

def _get_depa(cr,uid,partner,ids,gln):
    if partner.search(cr,uid,[('shop_iln','=',gln)]):
        ids.append(partner.search(cr,uid,[('shop_iln','=',gln)])[0])
    return ids


def seldepa(self, cr, uid, context={}):
    logger = netsvc.Logger()
    partner = pooler.get_pool(cr.dbname).get('res.partner')
    
#GLN 7301005110002 DE Helsingborg
#GLN 7301005120001 LE Umeå
#GLN 7301005130000 SP Uppsala
#GLN 7301005140009 LE Borlänge
#GLN 7301005150008 LE Helsingborg
#GLN 7301005190042 Färsk Kallhäll
#GLN 7301005230007 LE Kungälv
#GLN 7301005240006 SP Linköping
#GLN 7301005240013 SP Jönköping
#GLN 7301005240037 SP Kalmar
#GLN 7301005310006 SP Örebro
#GLN 7301005320005 SP Västerås
    depaer = []
    depaer = _get_depa(cr,uid,partner,depaer,'7301005110002')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005120001')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005130000')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005140009')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005150008')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005190042')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005230007')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005240006')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005240013')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005240037')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005310006')
    depaer = _get_depa(cr,uid,partner,depaer,'7301005320005')

    depa = partner.read(cr,uid,depaer,['name','id'],context)
    res = [(r['id'],r['name']) for r in depa]
    
    logger.notifyChannel("Critical", netsvc.LOG_CRITICAL,"Depå '%s' %s." % (res,depaer))

    return res



print_form = """<?xml version="1.0"?>
<form string="Skriv ut etiketter">
	<separator colspan="4" string="Välj depå och grupp" />
    <field name="utskriftsgrupp" />
</form>
"""
#	<field name="depa_id" />


print_fields = {
#    'depa_id': {'string': 'Depå', 'type': 'selection',  'selection': seldepa, 'required': True,  'default': lambda *a:'1704'},
    'utskriftsgrupp':{
        'string':"Utskriftsgrupp",
        'type':'selection',
        'selection':[('1','1 Delad frukt'),('2','2 Tråg/flowpack'),('3','3 1000 ml juice'),('4','4 350 ml juice')],
        'required': True,
        'default': lambda *a:'1'
    },
}


def partner_adr(cr,uid,EAN):
    partner = pooler.get_pool(cr.dbname).get('res.partner').read(cr,uid,pooler.get_pool(cr.dbname).get('res.partner').search(cr,uid,[("Shop_iln","=",EAN)]))
    
    if not partner:
        return EAN

    addr =  {}
    for addr_rec in pooler.get_pool(cr.dbname).get('res.partner.address').read(cr,uid, partner[0]['address'] ):
        addr[addr_rec['type']] = addr_rec

    adress = addr.get('delivery',addr.get('default',{'street': 'Street','zip':'Zip','city':'City'}))
    for i in ['street','zip','city']:
        if not adress[i]:
            adress[i]=''
    
    txt = unicode('"' + partner[0]['name'] + '\\n' + adress['street'] + '\\n' + adress['zip'] + ' ' + adress['city'] + '"')
    txt.replace(',',' ')  # Tar bort ev störande komman för csv-användningen
    
    return txt

class ica_label_print(wizard.interface):

    def _printLabels(self, cr, uid, data, context):
        logger = netsvc.Logger()
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal').read(cr,uid,data['id'])
 
        eanconsignee = pooler.get_pool(cr.dbname).get('res.partner').read(cr,uid,journal['partner_id'][0],['shop_iln'])

        #cr.execute("""
            #select distinct deldateshop from ica_label where  eanconsignee = '%s' and utskriftsgrupp = '%s' and ica_mrpjournal = %d                                    
                            #order by deldateshop desc""" % (eanconsignee['shop_iln'], data['form']['utskriftsgrupp'],data['id']))
        cr.execute("""
            select distinct deldateshop from ica_label                            
                            order by deldateshop desc""")
 
 
        deldateshop = cr.fetchall()
        logger.notifyChannel("Information", netsvc.LOG_INFO,"Deldateshop '%s'" % (deldateshop))
          
        labels = []
        # detta per deldateshop nyast datum först
        for date in deldateshop:
                   
            cr.execute("""
                select id from ica_label where  eanconsignee = '%s' and utskriftsgrupp = '%s' and ica_mrpjournal = %d and 
                                               utlevomr = '01'  and deldateshop = '%s' and
                                               (lass ~ '[1-7]0[1-9]' or lass ~ '[1-7]1[0-3]' or lass ~ '[1-7]1[5-9]' or lass ~ '[1-7]2[0-4]')
                                order by utskriftsprio""" % (eanconsignee['shop_iln'], data['form']['utskriftsgrupp'],data['id'],date[0]))
            labels1 = cr.fetchall()
            cr.execute("""select id from ica_label where  eanconsignee = '%s' and utskriftsgrupp = '%s' and ica_mrpjournal = %d and 
                                                                utlevomr = '01' and deldateshop = '%s' and  not
                                                                (lass ~ '[1-7]0[1-9]' or lass ~ '[1-7]1[0-3]' or lass ~ '[1-7]1[5-9]' or lass ~ '[1-7]2[0-4]')
                                order by utskriftsprio""" % (eanconsignee['shop_iln'], data['form']['utskriftsgrupp'],data['id'],date[0]))
            labels2 = cr.fetchall()
            cr.execute("""select id from ica_label where  eanconsignee = '%s' and utskriftsgrupp = '%s' and ica_mrpjournal = %d and 
                                                                utlevomr <> '01'  and deldateshop = '%s'
                                order by utskriftsprio""" % (eanconsignee['shop_iln'], data['form']['utskriftsgrupp'],data['id'],date[0]))
            labels3 = cr.fetchall()            
            
            #cr.execute("""
                #select id from ica_label where  deldateshop = '%s' and
                                               #(lass ~ '[1-7]0[1-9]' or lass ~ '[1-7]1[0-3]' or lass ~ '[1-7]1[5-9]' or lass ~ '[1-7]2[0-4]')
                                #order by utskriftsprio""" % (date))
            #labels1 = cr.fetchall()
            #cr.execute("""select id from ica_label where  deldateshop = '%s' and  not
                                                                #(lass ~ '[1-7]0[1-9]' or lass ~ '[1-7]1[0-3]' or lass ~ '[1-7]1[5-9]' or lass ~ '[1-7]2[0-4]')
                                #order by utskriftsprio""" % (date))
            #labels2 = cr.fetchall()
            #cr.execute("""select id from ica_label where  deldateshop = '%s'
                                #order by utskriftsprio""" % (date))
            #labels3 = cr.fetchall()
            logger.notifyChannel("print_labels", netsvc.LOG_INFO,"Deldateshop date '%s' labels %s" % (date,labels1 + labels2 + labels3))

            
            labels = labels + labels1 + labels2 + labels3
            
        logger.notifyChannel("print_labels", netsvc.LOG_INFO,"Labels '%s'" % (labels))

        jobname = "dj%03d-%s-%s" % (data['id'],eanconsignee['shop_iln'],data['form']['utskriftsgrupp'])
        os.system('mkdir /tmp/%s' % jobname)
        glabels = open("/tmp/%s/labels.csv" % jobname, "w")

        for id in labels:
            logger.notifyChannel("print_labels", netsvc.LOG_INFO,"id '%s' '%s' '%s' " % (id,id[0],id[:-1]))
            
            label = pooler.get_pool(cr.dbname).get('ica.label').read(cr,uid,id)
            product = pooler.get_pool(cr.dbname).get('product.product').read(cr,uid,label[0]['product_id'][0])

            utlevvecka = datetime.datetime.strptime(label[0]['deldateshop'],'%Y-%m-%d').strftime('%W')
            utlevdag = datetime.datetime.strptime(label[0]['deldateshop'],'%Y-%m-%d').strftime('%w')
            if utlevdag == '0':
                utlevdag = '7'

            product['name'].replace(',',' ')  # tar bort ev csv-störande tecken
            image = '/tmp/%s/%s.png' % (jobname,label[0]['sscc'])  

            txt = partner_adr(cr,uid,label[0]['eansender']).encode('utf-8')+","		# 01
            txt +=partner_adr(cr,uid,label[0]['eandelivery']).encode('utf-8')+','	# 02
            txt +=product['su_articlecode'].encode('utf-8')+','						# 03
            txt +="%09d" % id + ','                                                 # 04
            txt +='"%s",' % (product['name'].encode('utf-8'))						# 05
            txt +=label[0]['plockid'].encode('utf-8')+','							# 06
            
            txt +=label[0]['customernumber'].encode('utf-8')+','					# 07
            txt +="%d" % len(labels)+','                 							# 08
            txt +="%02d %s" % (int(utlevvecka),utlevdag) + ','                      # 09
            txt +="%03d/%02d" % (int(label[0]['lass']),int(label[0]['pl']))+','		# 10
            txt +="%02d/%02d" % (int(label[0]['utlevomr']),int(label[0]['port']))+',' # 11
            txt +="%03d-%03d" % (int(label[0]['ruta1']),int(label[0]['ruta2']))+','	# 12
            
            txt +=partner_adr(cr,uid,label[0]['eanshop']).encode('utf-8')+','		# 13
            txt +="%d" % label[0]['pallet_no']+','									# 14
            txt +=label[0]['typeofpackage'].encode('utf-8')+','						# 15
            txt +=label[0]['sscc'].encode('utf-8')+','								# 16
            txt +='[00]'+label[0]['sscc'].encode('utf-8')+','						# 17
            txt +=image.encode('utf-8')                                             # 18	Package image
        
            os.system('/usr/local/bin/zint --notext -o "/tmp/%s/%s.png" --barcode=16 -d %s' % (jobname,label[0]['sscc'],"[00]"+label[0]['sscc']))
            glabels.write('%s\n' % txt)

            # Beräkna antal kolli: per dagjournal per sale.order  count(customernumber)
            cr.execute("select count(id) from ica_label where ica_mrpjournal = %d and order_id = %d" % (data['id'],label[0]['order_id'][0]))
            bundle_qty = cr.fetchall()[0]                        
            logger.notifyChannel("print_labels", netsvc.LOG_INFO,"bundle_qty '%s'" % (bundle_qty))
            res = pooler.get_pool(cr.dbname).get('ica.label').write(cr,uid,[id[0]], {'bundle_qty': bundle_qty[0], 'date_printed': datetime.datetime.today() })
            pooler.get_pool(cr.dbname).get('ica.mrpjournal').write(cr,uid,data['id'], {'labels_printed':  datetime.datetime.today(), 'status': 'e' })
            logger.notifyChannel("print_labels", netsvc.LOG_INFO,"write ica.label '%s' '%s' '%s' '%s'" % (res,datetime.datetime.today(),len(labels),id[0]))

        cr.commit()
        glabels.close()
        os.system('glabels-batch -i /tmp/%s/labels.csv -o /tmp/%s/labels.ps /usr/share/greenvision/ica-small.glabels' % (jobname,jobname))
        os.system('ps2pdf /tmp/%s/labels.ps /var/spool/greenvision/labels/%s.pdf' % (jobname,jobname))
        #os.system('lp -o PageSize=w142h328 -o fitplot=false  /var/spool/greenvision/labels/%s.pdf' % (jobname))        
        os.system('lp -o PageSize=w142h328   /var/spool/greenvision/labels/%s.pdf' % (jobname))        
        os.system('rm -r /tmp/%s' % jobname)
        raise osv.except_osv(_('Utskrift klar'), _('Utskriften %s med %d etiketter klar') % (jobname,len(labels)))
        
        return {}



    states = {
            'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : print_form,
                    'fields' : print_fields,
                    'state' : [('end', 'Cancel'),('labels', 'Print labels') ]}
        },

        'labels' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _printLabels,
                    'state' : 'end'}
        },
 
        }
ica_label_print("ica.label_print")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
