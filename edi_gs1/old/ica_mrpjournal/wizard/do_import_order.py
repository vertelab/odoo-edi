
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
