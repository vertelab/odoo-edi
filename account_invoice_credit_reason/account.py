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
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    credited_period_start = fields.Date(string='Credited Period Start')
    credited_period_end = fields.Date(string='Credited Period End')
    credit_reason = fields.Selection(selection=[
        ('108', 'Finansiell kompensation'),
        ('140', 'Returer'),
        ('141', 'Volymrabatt'),
        ('79E', 'Felleverans'),
        ('Z01', 'Skadat gods'),
        ('Z02', 'Felbeställning'),
        ('Z03', 'Kvalitetsbrist'),
        ('Z04', 'Fel pris'),
    ], string='Credit Reason')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
