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
#########################################################################id###
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)



class sale_order(models.Model):
    _inherit='sale.order'
    
    edi_message_id = fields.Many2one(string="EDI Message",comodel_name='edi.message')
    
    @api.one
    def edi_import(self,edi_message_id):
        edi = self.env['edi.message'].browse(edi_message_id)
        order = self.env['sale.order'].create(edi.get('sale.order'))
        for line in edi.get('sale.order.line'):
            line['order_id'] = order.id
            self.env['sale.order.line'].create(line)
        self.env['mail.message'].create({
                'body': _("Imported EDI %s" % edi.name),
                'subject': 'Created from EDI-message',
                'author_id': order.partner_id.id,
                'res_id': order.id,
                'model': order._name,
                'type': 'notification',
            })
        order.edi_message_id = edi.id
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
