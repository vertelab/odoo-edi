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
# edi_message_type - Extension of edi.message.type for IPF REST and MQ

from odoo import models, fields, api, _
#from odoo.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

class edi_message_type(models.Model):
    _inherit = 'edi.message.type' 
    
    type_target = fields.Char(string='Target',help="If you need help you shouldn't be changing this")
    type_mapping = fields.Text(string='Data mapping',help="If you need help you shouldn't be changing this")

 # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: