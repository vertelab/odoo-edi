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
import json

import logging

_logger = logging.getLogger(__name__)


class EdiRoute(models.Model):
    _inherit = "edi.route"

    route_type = fields.Selection(
        selection_add=[
            ("edi_af_aisf_trask_rask", "AF AS rask"),
            ("edi_af_aisf_trask_office", "AF AS office"),
            ("edi_af_aisf_trask_contact", "AF AS contact"),
        ]
    )

    def _rask_get_all(self, message, res):
        # Get the answer from the call to AIS-F RASK
        res_set = message.env["edi.message"]

        body = json.dumps(res)
        vals = {
            "name": "RASK get all reply",
            "body": body,
            "edi_type": message.edi_type.id,
            "res_id": message.res_id,
            "route_type": message.route_type,
        }
        res_message = message.env["edi.message"].create(vals)
        res_message.unpack()

    def _asok_contact(self, message, res):
        # Why does these not update?
        message.state = "received"
        message.envelope_id.state = "received"

    def _asok_office(self, message, res):
        # Get the answer from the call to AIS-F RASK
        self._rask_get_all(message, res)


class EdiEnvelope(models.Model):
    _inherit = "edi.envelope"

    route_type = fields.Selection(
        selection_add=[
            ("edi_af_aisf_trask_rask", "AF AS rask"),
            ("edi_af_aisf_trask_office", "AF AS office"),
            ("edi_af_aisf_trask_contact", "AF AS contact"),
        ]
    )


class EdiMessage(models.Model):
    _inherit = "edi.message"

    route_type = fields.Selection(
        selection_add=[
            ("edi_af_aisf_trask_rask", "AF AS rask"),
            ("edi_af_aisf_trask_office", "AF AS office"),
            ("edi_af_aisf_trask_contact", "AF AS contact"),
        ]
    )

    def _generate_headers(self, af_tracking_id):
        get_headers = super(EdiMessage, self)._generate_headers(af_tracking_id)
        if self.edi_type in [
            self.env.ref("edi_af_aisf_trask.asok_office"),
            self.env.ref("edi_af_aisf_trask.asok_patch_office"),
            self.env.ref("edi_af_aisf_trask.asok_contact"),
        ]:
            # X-JWT-Assertion eller alternativt Authorization med given
            # data och PISA_ID med antingen sys eller handläggares signatur
            get_headers.update(
                {
                    "Authorization": self.route_id.af_authorization_header,
                    "PISA_ID": "*sys*",
                }
            )
        return get_headers
