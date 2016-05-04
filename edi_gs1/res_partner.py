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
import re, urllib2, base64, unicodecsv as csv #pip install unicodecsv
import os
import openerp.tools as tools
from openerp.modules import get_module_path

import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit='res.partner'

    gs1_gln = fields.Char(string="Global Location Number",help="GS1 Global Location Number (GLN)", select=True)
    role = fields.Char(string="Role",help="Chain or type of shop", select=True)
    customer_no = fields.Char(string="Customer No",help="The Customer No of the chain", select=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
