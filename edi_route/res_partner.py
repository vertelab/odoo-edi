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

class res_partner(models.Model):
    _inherit='res.partner'
    
    route_ids = fields.Many2many(comodel_name='edi.route')
    
    @api.one
    def _message_count(self):
        self.message_count = len(self.message_ids)
    message_count = fields.Integer(compute='_message_count',string="# messages")
    @api.one
    def _message_ids(self):
        #raise Warning([(6,0,[p.id for p in self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])])])
#        self.message_ids = self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])
       # self.message_ids = [p.id for p in self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])]
        self.message_ids = [(6,0,[p.id for p in self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])])]
    message_ids = fields.Many2many(compute='_message_ids',comodel_name="edi.message",string="Messages")    

    @api.model
    def get_routes(self,partner):  # own routes are of higher precedence than routes from parent
        if partner.parent_id:
            routes = {r.edi_type: r.id for r in partner.parent_id.route_ids}
        else:
            routes = {}
        for r in partner.parent_id.route_ids:
            routes[r.edi_type] = r.id
        #raise Warning(routes)
        return routes


from openerp import http
from openerp.http import request


class res_partner_controller(http.Controller):

    @http.route(['/partner/<model("res.partner"):partner>/test'], type='http', auth="public", website=True)
    def partner_test(self, partner=False, **post):
        if partner:
            return partner.name

    @http.route(['/partner/<model("res.partner"):partner>/json'], type='json', auth="public",)
    def partner_json(self, partner=False, **post):
        if partner:
            return partner.name


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
