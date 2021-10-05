# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEnvelopeRest(models.Model):
    _inherit = "edi.envelope"

    def get_headers(self):
        return {}

    def send(self):
        for rec in self:
            if (
                rec.route_id.protocol == "rest"
                and rec.route_id.rest_api == self.env.ref("api_rest_kontorsdatabasen")
            ):
                rec.send_kontorsdatabasen()

    def send_kontorsdatabasen(self):
        for msg in self.message_ids:
            if msg._name == "res.partner":
                pass
            elif msg._name == "hr.department":
                pass
            # partner = False
            # fill endpoint string with call data
            # endpoint = envelope.type_id.rest_endpoint.format({"forename": partner.name})
            endpoint = ""

            url = self.url + endpoint
            method = envelope.type_id.method
            data = {}  # no data for this request
            headers = envelope.get_headers()  # move to edi.type?

            self._call_endpoint(method, url, data_vals, headers)
