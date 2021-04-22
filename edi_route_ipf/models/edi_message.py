# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2021 Vertel AB (<http://vertel.se>).
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


class EdiMessage(models.Model):
    _inherit = "edi.message"
    """ IPF: Changes to message to allow communication with IPF 

    Implementations of new messages should inherit this class
    In their respective modules and extend functionality of 
    the function _generate_headers() to add special headers
    required for that message."""

    def _generate_headers(self, af_tracking_id):
        """This method generates headers and are used to call IPF in edi.route
        HINT:
         - use self to reach data on message
         - use self.route_id to reach data on the route
        """
        get_headers = {
            "AF-Environment": self.route_id.af_environment,
            "AF-SystemId": self.route_id.af_system_id,
            "AF-TrackingId": af_tracking_id,
            "AF-EndUserId": "*sys*",
        }
        return get_headers
