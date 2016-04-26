# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.tools as tools
from openerp.modules import get_module_path
from cStringIO import StringIO
import base64
from openpyxl import load_workbook
import os


import logging
_logger = logging.getLogger(__name__)

#~ try:
    #~ import openpyxl
#~ except ImportError:
    #~ raise Warning('excel library missing, pip install openpyxl')



class import_res_partner_axfood(models.TransientModel):
    _name = 'res.partner.axfood'

    data = fields.Binary('File')
    @api.one
    def _data(self):
        self.xml_file = self.data
    xml_file = fields.Binary(compute='_data')
    state =  fields.Selection([('choose', 'choose'), ('get', 'get')],default="choose")
    result = fields.Text(string="Result",default='')

#~ """
#~ Butik
#~ Ägandeform
#~ Kedja
#~ Status
#~ Telefon
#~ Organisationsnr
#~ Kund id
#~ GLN
#~ Direkt Lev. Fakt.
#~ Leveransadress
#~ Ort (leveransadress)
#~ Postnr (leveransadress)
#~ Butiksadress
#~ Ort (butiksadress)
#~ Postnr (butiksadress)
#~ Postadress
#~ Ort (postadress)
#~ Postnr (postadress)
#~ """
   
    @api.multi
    def send_form(self,):
        def _get_logo(img):
            return open(os.path.join(get_module_path('edi_gs1_coop'), 'static', 'img', img), 'rb').read().encode('base64')

        
        
        chart = self[0]
        #_logger.warning('data %s b64 %s ' % (account.data,base64.decodestring(account.data)))
        #raise Warning('data %s b64 %s ' % (chart.data.encode('utf-8'),base64.decodestring(chart.data.encode('utf-8'))))
        
        if not chart.data == None:
            
            wb = load_workbook(filename = StringIO(base64.b64decode(chart.data)), read_only=True)
            ws = wb[wb.get_sheet_names()[0]]
            t = tuple(ws.rows)
            title = [p.value for p in list(t[4])]

            i = 0
            for r in ws.rows:
                i += 1
                if i < 6:
                    continue
                l = {title[n]: r[n].value for n in range(len(r))}
                partner = self.env['res.partner'].search([('customer_no', '=', l['Butiksnr']),('parent_id','=',self.env.ref('edi_gs1_coop.coop').id)])
                record = {
                    'name': l['Butik'],
                    'role': l['Rangebox'],
                    'customer_no': l['Butiksnr'],
                    'city': l['Postadress'],
                    'zip': l['Postnummer'],
                    'country_id': self.env.ref('base.se').id,
                    'parent_id': self.env.ref('edi_gs1_coop.coop').id,
                    'is_company': True,
                    'customer': True,
                    'image': _get_logo('%s.png' % l['Rangebox']),
                    }
                if partner:
                    partner[0].write(record)
                    parent_id = partner[0].id
                else:
                    parent_id = self.env['res.partner'].create(record).id
                           
            return True
        chart.write({'state': 'get','result': 'All well'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'import.chart.template',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': chart.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
