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
from odoo.http import request
from odoo import SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.one
    def write(self, vals):
        # Overwrite write method to catch changes to user_id
        if self.is_jobseeker:
            user_id = vals.get("user_id", False)
            request = self._get_request_object()
            if request:
                current_user = request.env.user.id
            else:
                current_user = self.env.user.id
            if user_id and user_id != current_user and current_user != SUPERUSER_ID:
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


    def _get_request_object(self):
        """ Fetch the current request object, if one exists. We often run
        this code in sudo, so self.env.user is not reliable, but the
        request object always has the actual user.
        """
        try:
            # Poke the bear
            request.env
            # It's alive!
            return request
        except Exception:
            # No request is available
            return False
