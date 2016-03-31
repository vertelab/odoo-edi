# -*- encoding: utf-8 -*-
##############################################################################
#
#    Azzar.se  anders.wallenquist@vertel.se
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


from osv import osv
from osv import fields
import datetime

class ica_import_order(osv.osv):
    _name = "ica.import_order"
    _description = "Import Order"
    _columns = {
        'blob': fields.text('Textmessage'),
        'status': fields.selection((('n','Unconfirmed'), ('c','Confirmed'), ('e','Error')), 'Status', size=10),
        'date': fields.datetime('Datum',),
        'mrpjournal_id': fields.integer("Produktionsjournal",),
        'saleorder_id': fields.integer("Kundorder",),
    }
    _defaults = {
        'status': lambda *a: 'n',
        'mrpjournal_id': lambda *a: 0,
        'saleorder_id': lambda *a: 0,
    }
ica_import_order()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
