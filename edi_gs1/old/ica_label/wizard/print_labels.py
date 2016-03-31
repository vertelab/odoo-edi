
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

class ica_label_single_print(wizard.interface):

    def _printLabels(self, cr, uid, data, context):
        logger = netsvc.Logger()
        journal = pooler.get_pool(cr.dbname).get('ica.mrpjournal')

        logger.notifyChannel("Information", netsvc.LOG_INFO,"Label ids '%s' id '%s'" % (data['ids'],data['id']))

        jobname = "lbl%09d" % (data['id'])
        os.system('mkdir /tmp/%s' % jobname)
        glabels = open("/tmp/%s/labels.csv" % jobname, "w")

        for id in data['ids']:
            label = pooler.get_pool(cr.dbname).get('ica.label').read(cr,uid,id)
            product = pooler.get_pool(cr.dbname).get('product.product').read(cr,uid,label['product_id'][0])

            utlevvecka = datetime.datetime.strptime(label['deldateshop'],'%Y-%m-%d').strftime('%W')
            utlevdag = datetime.datetime.strptime(label['deldateshop'],'%Y-%m-%d').strftime('%w')
            if utlevdag == '0':
                utlevdag = '7'

            product['name'].replace(',',' ')  # tar bort ev csv-störande tecken
            image = '/tmp/%s/%s.png' % (jobname,label['sscc'])  

            txt = partner_adr(cr,uid,label['eansender']).encode('utf-8')+","		# 01
            txt +=partner_adr(cr,uid,label['eandelivery']).encode('utf-8')+','   	# 02
            txt +=product['su_articlecode'].encode('utf-8')+','						# 03
            txt +="%09d" % id + ','                                                 # 04
            txt +='"%s",' % (product['name'].encode('utf-8'))							# 05
            txt +=label['plockid'].encode('utf-8')+','							    # 06
            
            txt +=label['customernumber'].encode('utf-8')+','					    # 07
            txt +="%d" % len(data['ids'])+','							            # 08
            txt +="%02d %s" % (int(utlevvecka),utlevdag) + ','                      # 09
            txt +="%03d/%02d" % (int(label['lass']),int(label['pl']))+','		# 10
            txt +="%02d/%02d" % (int(label['utlevomr']),int(label['port']))+',' # 11
            txt +="%03d-%03d" % (int(label['ruta1']),int(label['ruta2']))+','	# 12
            
            txt +=partner_adr(cr,uid,label['eanshop']).encode('utf-8')+','		# 13
            txt +="%d" % label['pallet_no']+','									# 14
            txt +=label['typeofpackage'].encode('utf-8')+','						# 15
            txt +=label['sscc'].encode('utf-8')+','								# 16
            txt +='[00]'+label['sscc'].encode('utf-8')+','						# 17
            txt +=image.encode('utf-8')                                             # 18	Package image
        
            os.system('/usr/local/bin/zint --notext -o "/tmp/%s/%s.png" --barcode=16 -d %s' % (jobname,label['sscc'],"[00]"+label['sscc']))
            glabels.write('%s\n' % txt)
            
            pooler.get_pool(cr.dbname).get('ica.label').write(cr,uid,[id], {'date_printed': datetime.datetime.today() })


        glabels.close()
        os.system('glabels-batch -i /tmp/%s/labels.csv -o /tmp/%s/labels.ps /usr/share/greenvision/ica-small.glabels' % (jobname,jobname))
        os.system('ps2pdf /tmp/%s/labels.ps /var/spool/greenvision/labels/%s.pdf' % (jobname,jobname))
        os.system('lp -o PageSize=w142h328 -o fitplot=false  /var/spool/greenvision/labels/%s.pdf' % (jobname))        
        #os.system('lp -o PageSize=w142h328   /var/spool/greenvision/labels/%s.pdf' % (jobname))        
        os.system('rm -r /tmp/%s' % jobname)
        raise osv.except_osv(_('Utskrift klar'), _('Utskriften %s med %d etiketter klar') % (jobname,len(data['ids'])))
        
        return {}



    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _printLabels,
                    'state' : 'end'}
        },
 
    }
ica_label_single_print("ica.label_single_print")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
