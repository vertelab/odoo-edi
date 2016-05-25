# -*- coding: utf-8 -*-
from openpyxl import load_workbook
import odoorpc

params = odoorpc.session.get('paolos')
odoo = odoorpc.ODOO(params.get('host'),port=params.get('port'))
odoo.login(params.get('database'),params.get('user'),params.get('passwd'))

wb = load_workbook(filename = 'doc/KUNDREGISTER 2016.xlsx', read_only=True)
ws = wb['TOTAL']
row = tuple(ws.rows)

def _get_categ_id(categ):
    c = odoo.env['res.partner.category'].search([('name', '=', categ)])
    if len(c) == 0:
        odoo.env['res.partner.category'].create({'name': categ})
    return odoo.env['res.partner.category'].search([('name', '=', categ)])

for i in range(1, 2160):
    line = {}
    for column in range(len(row[0])):
        line[u'%s' %row[0][column].value] = u'%s' %row[i][column].value
    gs1_gln = line.get('LOKKOD')
    if gs1_gln != 'None':
        #~ print gs1_gln
        partner_values = {
            'customer_no': line.get('IDNR'),
            'name': line.get('JURIDNAMN'),
            'street': line.get('BESADR'),
            'zip': line.get('POSTNR1'),
            'city': line.get('ORT1'),
            'phone': line.get('TELEFON'),
            'fax': line.get('FAX'),
            #~ 'chef': line.get('BUTIKSCHEF'),
            'areg': line.get('AREG'),
            'role': line.get('KEDJATXT'),
            #~ 'turnover': line.get('STORLEK'),
            'vat': 'SE' + line.get('ORGNR') + '01',
            'gs1_gln': line.get('LOKKOD'),
            'category_id': [(6, False, _get_categ_id(line.get('REGION')))],
            #~ 'salesman': line.get('SÄLJARE'),
            'store_class': line.get('BUTIKSKLASS') if line.get('BUTIKSKLASS') != 'None' else '',
            #~ 'fgs_paolos': line.get('FSG PAOLOS'),
            #~ 'fgs_leroy': line.get('FSG LERÖY'),
        }

        #~ print partner_values

        p = odoo.env['res.partner'].read(odoo.env['res.partner'].search([('gs1_gln', '=', gs1_gln)]),['gs1_gln'])
        if p:
            print 'Partner %s update' %p[0]['id']
            odoo.env['res.partner'].write(p[0]['id'], partner_values)
        else:
            print 'Partner create'
            odoo.env['res.partner'].create(partner_values)





