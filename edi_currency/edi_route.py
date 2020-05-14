# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
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
import base64
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class edi_envelope(models.Model):
    _inherit = 'edi.envelope' 
    
    @api.one
    def fold(self,route): # Folds messages in an envelope
        for m in self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',route.id)]):
            m.envelope_id = self.id
        envelope = super(edi_envelope,self).fold(route)
        return envelope

class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    route_type = fields.Selection(selection_add=[('get exchange rate','Get Exchange Rate')])

class edi_message(models.Model):
    _inherit='edi.message'
          

