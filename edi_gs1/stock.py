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

class stock_picking(models.Model):
    _inherit = "stock.picking"
        
    def _edi_message_create(self,edi_type):
        if self.partner_id and self.partner_id.parent_id: 
            if edi_type in [r.edit_type for r in self.partner_id.parent_id.edi_route_ids]: # Parent customer has route for this message type
                if not self.env['edi.message'].search([('model','=',self._name),('res_id','=',self.id),('edi_type','=',edi_type)]): # Just one message per sale.order and type
                    routes = {r.edi_type: r.id for r in self.partner_id.parent_id.edi_route_ids}
                    message = self.env['edi.message'].create({
                            'name': self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_message').id),
                            'edi_type': edi_type,
                            'model': self._name,
                            'res_id': self.id,
                            'route_id': routes[edi_type]
                    })
                    message.pack()
                    self.env['mail.message'].create({
                            'body': _("%s %s created" % (edi_type,message.name)),
                            'subject': edi_type,
                            'author_id': self.user_id.partner_id.id,
                            'res_id': self.id,
                            'model': self._name,
                            'type': 'notification',})                

    @api.one
    def action_create_desadv(self):
        # Create SCCS-number ?
        self._edi_message_create('DESADV')

    @api.one
    def action_done(self):
        self.action_create_desadv()        
        return super(stock_picking,self).action_done()
        
    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
