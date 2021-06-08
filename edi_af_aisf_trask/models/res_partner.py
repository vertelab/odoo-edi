# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.one
    def write(self, vals):
        # Overwrite write method to catch changes to user_id
        user_id = vals.get("user_id", False)
        if user_id and user_id != self.env.user.id:
            if user_id != self.user_id.id:
                route = self.env.ref("edi_af_aisf_trask.asok_office_route")

                msg_vals = {
                    "name": "patch office msg",
                    "edi_type": self.env.ref("edi_af_aisf_trask.asok_patch_office").id,
                    "model": self._name,
                    "res_id": self.id,
                    "route_id": route.id,
                    "route_type": "edi_af_aisf_trask_office",
                }

                message = self.env["edi.message"].create(msg_vals)
                message.pack()
                route.run()

        super(ResPartner, self).write(vals)
