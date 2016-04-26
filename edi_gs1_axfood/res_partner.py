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



import logging
_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    raise Warning('excel library missing, pip install openpyxl')



class import_res_partner_axfood(models.TransientModel):
    _name = 'res.partner.axfood'

    data = fields.Binary('File')
    @api.one
    def _data(self):
        self.xml_file = self.data
    xml_file = fields.Binary(compute='_data')
    state =  fields.Selection([('choose', 'choose'), ('get', 'get')],default="choose")
    result = fields.Text(string="Result",default='')


   
    @api.multi
    def send_form(self,):
        chart = self[0]
        #_logger.warning('data %s b64 %s ' % (account.data,base64.decodestring(account.data)))
        raise Warning('data %s b64 %s ' % (chart.data.encode('utf-8'),base64.decodestring(chart.data.encode('utf-8'))))
        
        if not chart.data == None:
            
            wb = load_workbook(filename = cStringIO.StringIO(base64_decode(chart.data)), read_only=True)

            ws = wb['Blad1']

            #print wb.get_sheet_names()

            ws = wb[wb.get_sheet_names()[0]]
            t = tuple(ws.rows)
            title = [p.value for p in list(t[0])]

            for row in ws.rows:
                
            t = tuple(ws.rows)

            d = []
            for r in ws.rows:
                d.append({title[n]: r[n].value for n in range(len(r))})

            
            fileobj = TemporaryFile('w+')
            fileobj.write(base64.decodestring(chart.data))
            fileobj.seek(0)
            #~ try:
                #~ tools.convert_xml_import(account._cr, 'account_export', fileobj, None, 'init', False, None)
            #~ finally:
            fileobj.close()
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



############## ICA helper functions ##############
def utf_8_encoder(input):
    for line in input:
        yield line.decode('windows-1252').encode('utf-8')

def excel_remove_clutter(string):
    pattern = re.compile('=T\(".*"\)')
    if pattern.match(string):
        return string[4:-2]
    return string
##################################################

class res_partner(models.Model):
    _inherit='res.partner'

    #
    @api.model
    def ica_update_store_registry(self):
        request = urllib2.Request("https://levnet.ica.se/Levnet/ButRegLev.nsf/wwwviwButiksfil/frmButiksfil/$FILE/butreg.xls")
        #sudo?
        #TODO: Error handling for parameters
        username = self.env['ir.config_parameter'].get_param('ica.levnet.username')
        password = self.env['ir.config_parameter'].get_param('ica.levnet.password')
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)
        csv_data = csv.DictReader(utf_8_encoder(result), encoding='utf-8', dialect='excel', delimiter='\t')
        #"Företag", "Postadress", "Postnummer", "Ort", "Kundnummer",
        #"Lokaliseringskod, butik", "Lagerenhet", "Lokaliseringskod LE",
        #"Telefon", "Roll", "Lokaliseringskod godsadress", "Ändringsdatum"

        ica = self.env.ref('edi_gs1.ica_gruppen')
        if not ica:
            raise Warning("Couldn't find ICA central record (edi_gs1.ica_gruppen).")
        for row in csv_data:
            partner_values = {
                'name': excel_remove_clutter(row[u'Företag']),
                'gs1_gln': excel_remove_clutter(row[u'Lokaliseringskod, butik']),
                'street': excel_remove_clutter(row[u'Postadress']),
                'zip': excel_remove_clutter(row[u'Postnummer']),
                'city': excel_remove_clutter(row[u'Ort']),
                'phone': excel_remove_clutter(row[u'Telefon']),
                'ref': excel_remove_clutter(row[u'Kundnummer']),
                'parent_id': ica.id,
                'is_company': True,
                #~ 'foobar': excel_remove_clutter(csv_data[u'Lagerenhet']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Lokaliseringskod LE']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Roll']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Lokaliseringskod godsadress']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Ändringsdatum']),
            }
            partner = self.env['res.partner'].search([('gs1_gln', '=', partner_values['name'])])
            #Remove redundant values
            for key in partner_values:
                if partner and getattr(partner, key) == partner_values[key]:
                    del(partner_values[key])
            _logger.warn("partner_values: %s" %partner_values)
            if partner:
                if partner_values:
                    partner.write(partner_values)
            else:
                partner.create(partner_values)

    @api.model
    def ica_update_logo(self):
        def _get_logo(img):
            return open(os.path.join(get_module_path('edi_gs1'), 'static', 'img', img), 'rb').read().encode('base64')

        for p in self.env['res.partner'].search([]):
            if (u'ICA') in p.name and (u'Nära') in p.name:
                p.image = _get_logo('ica_nara.jpg')
            elif (u'ICA') in p.name and (u'Supermarket') in p.name:
                p.image = _get_logo('ica_supermarket.jpg')
            elif (u'Apotek') in p.name and (u'Hjärtat') in p.name:
                p.image = _get_logo('apotek_hjartat.png')
            elif (u'ICA') in p.name and (u'Kvantum') in p.name:
                p.image = _get_logo('ica_kvantum.jpg')
            elif (u'Maxi') in p.name:
                p.image = _get_logo('ica_maxi.jpg')
            elif (u'ICA') in p.name:
                p.image = _get_logo('ica_nara.jpg')
            elif (u'Coop') in p.name and (u'Extra') in p.name:
                p.image = _get_logo('coop_extra.jpg')
            elif (u'Coop') in p.name and (u'Forum') in p.name:
                p.image = _get_logo('coop_forum.png')
            elif (u'Coop') in p.name and (u'Konsum') in p.name:
                p.image = _get_logo('coop_konsum.png')
            elif (u'Coop') in p.name and (u'Nära') in p.name:
                p.image = _get_logo('coop_nara.jpg')
            elif (u'Hemköp') in p.name:
                p.image = _get_logo(u'hemkop.jpg')
            elif (u'Willys') in p.name and (u'Hemma') in p.name:
                p.image = _get_logo('willys_hemma.png')
            elif (u'Willys') in p.name:
                p.image = _get_logo(u'willys.gif')
            elif (u'Tempo') in p.name:
                p.image = _get_logo('tempo.png')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
