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

class ica_mrpjournal(osv.osv):
    _name = "ica.mrpjournal"
    _description = "Mrp Journal"
    _columns = {
#        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True, change_default=True, select=True),
#        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, required=True, change_default=True, select=True),
        'partner_id': fields.many2one('res.partner', 'Depå', select=True),
        'status': fields.selection((('i','EDI order'), ('s',"Kundorder"), ('o','Orderbekräftelse'),('e','Etiketter'),('l','Leveransbekräftelse'),('f','Faktura')), 'Status', size=10,),
        'datum': fields.date('datum', ),
        'produktion_startad': fields.datetime('Produktion startad', ),
        'produktion_avslutad': fields.datetime('Produktion avslutad', ),
        'packning_startad': fields.datetime('Packning startad', ),
        'packning_avslutad': fields.datetime('Packning avslutad', ),
        'labels_printed': fields.datetime('Etiketter', ),
        'saleorder_imported': fields.datetime('Kundorder skapade',),
        'saleorder_ordrsp': fields.datetime('Orderbekräftelse',),
        'saleorder_dspadv': fields.datetime('Leveransbekräftelse',),
        'saleorder_invoice': fields.datetime('Fakturerad',),
    }
    _defaults = {
        'status': lambda *a: 'i',
    }
ica_mrpjournal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
#• Lista
#• Sida
#• Fält
#        ◦ Datum
#        ◦ Produktion, startad
#        ◦ Produktion avslutad
#        ◦ Packning, startad
#        ◦ Packning avslutad
#        ◦ Levererad
#        ◦ Fakturerad
