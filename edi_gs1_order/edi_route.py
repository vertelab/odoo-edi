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

import logging
_logger = logging.getLogger(__name__)

               
class edi_envelope(models.Model):
    _inherit = 'edi.envelope' 
    
    @api.one
    def transform(self):
        pass
        
    
        
                
class edi_message(models.Model):
    _inherit = 'edi.message' 
    
    @api.one
    def get(self,record):
        if self.edi_type == 'orders':
            return edi.data[record]
    
    
    def _cron_job_in(self,cr,uid, edi, context=None):
        if edi.edi_type == 'order':
            self.pool.get('sale.order').edi_import(edi.id)
        if edi.edi_type == 'ordrsp':
            self.pool.get('sale.order').edi_import(edi.id)

        return super(edi_message,self)._cron_job_in(cr,uid,edi,context=context)

    def _cron_job_out(self,cr,uid, edi, context=None):
        if edi.edi_type == 'order':
            self.pool.get('sale.order').edi_export(edi.id)
        if edi.edi_type == 'ordrsp':
            self.pool.get('sale.order').edi_export(edi.id)

        return super(edi_message,self)._cron_job_out(cr,uid,edi,context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
