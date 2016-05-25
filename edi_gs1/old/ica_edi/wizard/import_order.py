# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
from osv import fields, osv
from tools.translate import _

form = """<?xml version="1.0"?>
<form string="Advance Payment">
    <field name="journal_id"/>
    <newline />
    <field name="qtty"/>
    <field name="amount"/>
    <newline />
</form>
"""
fields = {
        'journal_id': {'integer':'Journal', 'type':'many2one','relation':'ica.mrpjournal','required':True},
}

form_msg = """<?xml version="1.0"?>
<form string="Invoices">
   <label string="You invoice has been successfully created !"/>
</form>
"""
fields_msg = {}


class sale_edi_import_order(wizard.interface):
    def _open_invoice(self, cr, uid, data, context):
        pool_obj = pooler.get_pool(cr.dbname)
        model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),('name','=','invoice_form')])
        resource_id = pool_obj.get('ir.model.data').read(cr,uid,model_data_ids,fields=['res_id'])[0]['res_id']
        return {
            'domain': "[('id','in', ["+','.join(map(str,data['form']['invoice_ids']))+"])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False,'tree'),(resource_id,'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form' ,   'arch' : form,'fields' : fields,'state' : [('end','Cancel','gtk-cancel'),('create','Create Salesorder','gtk-ok')]}
        },
        'create': {
            'actions': [],
            'result': {'type' : 'form' ,'arch' : form_msg,'fields' : fields_msg, 'state':[('end','Close','gtk-close'),('open','Open Salesorder','gtk-open')]}
        },
        'open': {
            'actions': [],
            'result': {'type':'action', 'action':_open_invoice, 'state':'end'}
        }
    }
sale_edi_import_order("sale.edi_import_order")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

