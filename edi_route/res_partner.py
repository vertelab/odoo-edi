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

class res_partner(models.Model):
    _inherit='res.partner'

    #edi_type_ids = fields.Many2many(comodel_name='edi.message.type',help="OK to send EDI-messages of this type to this part")

    @api.one
    def _edi_message_count(self):
        self.edi_message_count = len(self.edi_message_ids)
    edi_message_count = fields.Integer(compute='_edi_message_count',string="# messages")

    @api.one
    def _edi_message_ids(self):
        #raise Warning([(6,0,[p.id for p in self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])])])
#        self.edi_message_ids = self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])
       # self.edi_message_ids = [p.id for p in self.env['edi.message'].search(['|','|','|',('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])]
        self.edi_message_ids = [(6,0,[p.id for p in self.env['edi.message'].search(['|','|','|','|','|',('sender','=',self.id),('recipient','=',self.id),('consignor_id','=',self.id),('consignee_id','=',self.id),('forwarder_id','=',self.id),('carrier_id','=',self.id)])])]
    edi_message_ids = fields.Many2many(compute='_edi_message_ids',comodel_name="edi.message",string="Messages")

    @api.model
    def get_edi_types(self, partner):
        """
            Check in n levels if its ok to send edi-messages of this type to this part.
            Check in edi_message._edi_message_create()
        """
        types = [l.edi_type.id for l in partner.edi_application_lines]
        if partner.parent_id:
            types += self.get_edi_types(partner.parent_id)
        return set(types)

    edi_application_lines = fields.One2many('edi.application.line', 'partner_id', 'EDI Applications')

from odoo import http
from odoo.http import request


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
