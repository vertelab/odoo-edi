#!/usr/bin/python
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



from openpyxl import load_workbook

wb = load_workbook(filename = 'Coop_Shops.xlsx', read_only=True)

ws = wb['Blad1']

#print wb.get_sheet_names()

ws = wb[wb.get_sheet_names()[0]]
t = tuple(ws.rows)

title = [p.value for p in list(t[0])]
d = []
for r in ws.rows:
    d.append({title[n]: r[n].value for n in range(len(r))})



print d


#record = {t[c][0].value: t[c][r].value [c,r for c,r in range(10),range(10)]}


title = [p.value for p in list(t[0])]

print title

l = list(t)
l.pop()
l.pop()

for row in l:
    for c in range(len(list(row))):
        print row[c].value
    exit()

print t[0][0].value

exit()


records = {}
for row in ws.rows:
    r = {}
    for cell in row:
        print cell.columns

exit()
for ws in wb._sheets:
    print ws.values()
exit()

for h in ws.columns:
    print h[0].value

for row in ws.rows:
    print row.print_titles()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
