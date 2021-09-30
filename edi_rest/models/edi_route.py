# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
from odoo.addons.edi_base.models.edi_error import EDIUnkownMessageError
from urllib import request
from urllib.error import HTTPError, URLError
import json
import ssl
import uuid

_logger = logging.getLogger(__name__)


class EdiRouteRest(models.Model):
    _inherit = "edi.route"

    url = fields.Char(string='URL')
    protocol = fields.Selection(selection_add=[('rest', 'REST')])
    rest_api = fields.Many2one(comodel_name='edi.rest.api', string='REST API')

    def run_out(self):
        res = super(EdiRouteRest, self).run_out()
        return res

    def run_in(self):
        res = super(EdiRouteRest, self).run_in()
        return res

    def _generate_tracking_id(self):
        """Returns an uuid to be used as a unique tracking id"""
        return str(uuid.uuid4())

    def _generate_ctx(self):
        """Generates a context for our calls"""
        ctx = ssl.create_default_context()
        if self.ssl_protocol == "no_verify":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if self.ssl_protocol == "mutual":  # mTLS
            # TODO: untested code, test this
            # Define the client certificate settings for https connection
            # https://www.techcoil.com/blog/how-to-send-a-http-request-with-client-certificate-private-key-password-secret-in-python-3/
            ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            ctx.load_cert_chain(certfile=self.ssl_certfile, keyfile=self.ssl_keyfile)
        elif self.ssl_protocol == "simple":
            # TODO: implement
            pass
        return ctx

    def _call_endpoint(self, method, url, data_vals, headers):
        """Handles calls to endpoints"""

        data_vals = json.dumps(data_vals).encode("utf-8")
        ctx = self._generate_ctx()
        req = request.Request(url=url, data=data_vals, headers=headers, method=method)
        try:
            res_json = request.urlopen(req, context=ctx).read()
        except Exception as e:
            # Log what request generated this error, but remove sensitive
            # information before sending it to log
            # censored_error = message.censor_error(
            #     url=url, headers=headers, method=method, data=data_vals
            # )
            # message.message_post(body=censored_error)
            _logger.exception(censored_error)
            raise e

        if res_json:
            res = json.loads(res_json)
        else:
            res = False
