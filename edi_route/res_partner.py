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
