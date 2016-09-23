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

def fix_zip(zip):
    res = ''
    for c in zip:
        res += c if c.isdigit() else ''
    if len(res) > 3:
        return '%s %s' % (res[:3], res[3:])
    return zip

def fix_city(city):
    if len(city) > 1:
        return '%s%s' % (city[0], city[1:].lower())
    return city

class import_res_partner_axfood(models.TransientModel):
    _name = 'res.partner.coop'

    data = fields.Binary('File')
    state =  fields.Selection([('choose', 'choose'), ('get', 'get')],default="choose")
    result = fields.Text(string="Result",default='')
    write_image = fields.Boolean('Overwrite logos')


   
    @api.multi
    def send_form(self,):
        def _get_logo(img):
            return open(os.path.join(get_module_path('edi_gs1_coop'), 'static', 'img', img), 'rb').read().encode('base64')
        
        self.ensure_one()
        if not self.data == None:
            
            wb = load_workbook(filename = StringIO(base64.b64decode(self.data)), read_only=True)
            ws = wb[wb.get_sheet_names()[0]]
            t = tuple(ws.rows)
            title = [p.value for p in list(t[4])]

            i = 0
            for r in ws.rows:
                i += 1
                if i < 6:
                    continue
                l = {title[n]: r[n].value for n in range(len(r))}
                if not l['Butiksnr']:
                    break
                partner = self.env['res.partner'].search([('ref', '=', l['Butiksnr']), ('parent_id', '=', self.env.ref('edi_gs1_coop.coop').id)])
                record = {
                    'name': l['Butik'],
                    'rangebox': l['Rangebox'],
                    'store_number': l['Butiksnr'],
                    'country_id': self.env.ref('base.se').id,
                    'parent_id': self.env.ref('edi_gs1_coop.coop').id,
                    'is_company': True,
                    'customer': True,
                    'ref': '',
                    }
                city = fix_city(l['Postadress'])
                zip = fix_zip(l['Postnummer'])
                if city:
                    record['city'] = city
                if zip:
                    record['zip'] = zip
                if self.write_image:
                    record['image'] = _get_logo('%s.png' % l['Rangebox'])
                if partner:
                    partner[0].write(record)
                    parent_id = partner[0].id
                else:
                    parent_id = self.env['res.partner'].create(record).id
                           
            return True
        self.write({'state': 'get','result': 'All well'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.coop',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
