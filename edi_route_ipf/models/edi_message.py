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
from urllib import parse
import logging

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    """IPF: Changes to message to allow communication with IPF

    Implementations of new messages should inherit this class
    in their respective modules and extend functionality of
    the method _generate_headers() to add special headers
    required for that message. Method censor_error() should also be
    overridden. """

    _inherit = "edi.message"

    def _generate_headers(self, af_tracking_id):
        """This method generates headers the that are used to call IPF in edi.route
        HINT:
         - use self to reach data on message
         - use self.route_id to reach data on the route"""

        get_headers = {
            "AF-Environment": self.route_id.af_environment,
            "AF-SystemId": self.route_id.af_system_id,
            "AF-TrackingId": af_tracking_id,
            "AF-EndUserId": "*sys*",
        }
        return get_headers

    @api.model
    def censor_error(self, url, headers, method, data=False):
        """ The Politburo.
        Responsible for removing sensitive information from error messages
        before it is published in logs and to users. This method needs to
        be overridden for each message type or the log will show the entire
        uncensored request in case of errors. """
        res = _(
            "Error while sending message: URL: {url} DATA: {data} HEADERS: {headers} METHOD: {method}"
        )
        censored_params = {
            'client_id': "REMOVED",
            'client_secret': "REMOVED"
        }

        # parse URL and update censured values.
        url_parts = list(parse.urlparse(url))
        query = dict(parse.parse_qsl(url_parts[4]))
        query.update(censored_params)
        url_parts[4] = parse.urlencode(query)
        url = parse.urlunparse(url_parts)

        res = res.format(url=url, data=data, headers=headers, method=method)
        return res
