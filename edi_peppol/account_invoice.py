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
from odoo.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    @api.one
    def _edi_message_create(self,edi_type):
        self.env['edi.message']._edi_message_create(edi_type=edi_type,obj=self,partner=self.partner_id,check_route=False,check_double=False)

    @api.one
    def action_create_invoic(self):
        self._edi_message_create('INVOIC')

    #~ @api.multi
    #~ def action_move_create(self):
        #~ for invoice in self:
            #~ invoice.action_create_invoic()   
        #~ return super(account_invoice,self).action_move_create()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
