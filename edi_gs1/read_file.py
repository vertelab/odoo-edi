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

def _get_store_chef(chef, parent_id):
    c = odoo.env['res.partner'].search(['&', ('name', '=', chef), ('parent_id', '=', parent_id)])
    if len(c) == 0:
        odoo.env['res.partner'].create({'name': chef, 'function': u'Butikchef', 'parent_id': parent_id, 'use_parent_address': True})

def _get_salesman(salesman, parent_id):
    s = odoo.env['res.users'].search([('name', '=', salesman)])
    if len(s) == 0:
        odoo.env['res.users'].create({'name': salesman, 'login': salesman, 'sel_groups_9_40_10': 9,})
    odoo.env['res.partner'].write(parent_id, {'user_id': odoo.env['res.users'].search([('name', '=', salesman)])[0]})

def _get_id_from_gln(gs1_gln):
    p = odoo.env['res.partner'].read(odoo.env['res.partner'].search([('gs1_gln', '=', gs1_gln)]),['id'])
    return p[0]['id']

for i in range(1984, 2160):
    line = {}
    for column in range(len(row[0])):
        line[u'%s' %row[0][column].value] = u'%s' %row[i][column].value
    gs1_gln = line.get(u'LOKKOD')
    if gs1_gln != 'None':
        partner_values = {
            'customer_no': line.get(u'IDNR'),
            'name': line.get(u'JURIDNAMN'),
            'street': line.get(u'BESADR'),
            'zip': line.get(u'POSTNR1'),
            'city': line.get(u'ORT1'),
            'phone': line.get(u'TELEFON'),
            'fax': line.get(u'FAX'),
            'areg': line.get(u'AREG'),
            'role': line.get(u'KEDJATXT'),
            'vat': 'SE' + line.get(u'ORGNR') + '01',
            'gs1_gln': line.get(u'LOKKOD'),
            'category_id': [(6, False, _get_categ_id(line.get(u'REGION')))],
            'store_class': line.get(u'BUTIKSKLASS') if line.get(u'BUTIKSKLASS') != 'None' else '',
            'is_company': True,
            'size': int(line.get('STORLEK') if line.get('STORLEK') != 'None' else 0) * 1.0,
            #~ 'fgs_paolos': int(line.get('FSG PAOLOS') if line.get('FSG PAOLOS') != 'None' else 0) * 1.0,
            #~ 'fgs_leroy': int(line.get('FSG LERÖY') if line.get('FSG LERÖY') != 'None' else 0) * 1.0,
        }
        #~ for key in partner_values:
            #~ print '%s:\t\t%s' % (key, partner_values[key])
        p = odoo.env['res.partner'].read(odoo.env['res.partner'].search([('gs1_gln', '=', gs1_gln)]),['gs1_gln'])
        if p:
            print 'Partner %s update' %p[0]['id']
            odoo.env['res.partner'].write(p[0]['id'], partner_values)
        else:
            print 'Partner create'
            odoo.env['res.partner'].create(partner_values)
        _get_store_chef(line.get(u'BUTIKSCHEF'), _get_id_from_gln(gs1_gln))
        _get_salesman(line.get(u'SÄLJARE'), _get_id_from_gln(gs1_gln))





