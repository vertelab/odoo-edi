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
import json

import logging

_logger = logging.getLogger(__name__)


class EdiEnvelope(models.Model):
    _inherit = "edi.envelope"

    route_type = fields.Selection(
        selection_add=[
            ("edi_af_as_notes_post", "AF asok notes post"),
            ("edi_af_as_notes_get", "AF asok notes get"),
        ]
    )


class EdiRoute(models.Model):
    _inherit = "edi.route"

    route_type = fields.Selection(
        selection_add=[
            ("edi_af_as_notes_post", "AF asok notes post"),
            ("edi_af_as_notes_get", "AF asok notes get"),
        ]
    )

    def _edi_af_as_notes_post(self, message, res):
        message.state = "received"


class EdiMessage(models.Model):
    _inherit = "edi.message"

    route_type = fields.Selection(
        selection_add=[
            ("edi_af_as_notes_post", "AF asok notes post"),
            ("edi_af_as_notes_get", "AF asok notes get"),
        ]
    )

    def _generate_headers(self, af_tracking_id):
        get_headers = super(EdiMessage, self)._generate_headers(af_tracking_id)
        if self.edi_type == self.env.ref("edi_af_as_notes.edi_af_as_notes_post"):
            # Authorization with given username+password and PISA_ID
            # using either sys or case workers signature
            get_headers.update(
                {
                    "Authorization": self.route_id.af_authorization_header,
                    # TODO: change this to signature
                    "PISA_ID": "*sys*",
                }
            )
        return get_headers

    def censor_error(self, url, headers, method, data=False):
        # Remove Authorization token from headers before logging message
        censored_headers = {
            "Authorization": "REMOVED",
        }
        headers.update(censored_headers)
        res = super(EdiMessage, self).censor_error(url, headers, method, data)
        return res
