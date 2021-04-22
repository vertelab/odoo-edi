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
from odoo.exceptions import Warning
from urllib import request
from urllib.error import HTTPError, URLError
import json
import ssl
import uuid
import ast

import logging

_logger = logging.getLogger(__name__)


class EdiRoute(models.Model):
    # TODO: maybe make this a new model sometime in the future
    # _name = "edi.route.ipf"
    _inherit = "edi.route"
    """ IPF: Class to communicate with IPF through REST

    Implementations of new messages should inherit this class
    In their respective modules and add a new function called
    "_<edi.message.type external_id (without module name)>"
    that handle the message type in order for the code to work.

    Functions for messages defined in the code in this file are a
    legacy that should be removed and moved to their respective
    modules in further iterations of this code."""

    # address
    af_ipf_url = fields.Char(
        string="IPF API URL", help="If you need help you shouldn't be changing this"
    )
    af_ipf_port = fields.Char(
        string="IPF API port", help="If you need help you shouldn't be changing this"
    )
    # id and secret
    af_client_id = fields.Char(
        string="Client Id", help="If you need help you shouldn't be changing this"
    )
    af_client_secret = fields.Char(
        string="Client secret", help="If you need help you shouldn't be changing this"
    )
    # headers
    af_environment = fields.Char(
        string="AF-Environment", help="If you need help you shouldn't be changing this"
    )
    af_system_id = fields.Char(
        string="AF-SystemId", help="If you need help you shouldn't be changing this"
    )
    af_authorization_header = fields.Char(
        string="AF-Authorization header",
        help="If you need help you shouldn't be changing this",
    )

    protocol = fields.Selection(selection_add=[("ipf", "IPF")])
    ssl_protocol = fields.Selection(
        selection=[
            ("no_verify", "No verification"),
            ("simple", "Simple verification"),
            ("mutual", "Mutual verification (mTLS)"),
        ],
        string="SSL-Protocol",
    )
    ssl_certfile = fields.Char(
        string="SSL Cert File Path",
        help="Path of the X.509 certificate file in PEM(Privacy Enhanced Email) format",
    )
    ssl_keyfile = fields.Char(
        string="SSL Key File Path",
        help="Path of the X.509 private key of the certificate",
    )
    # https://www.techcoil.com/blog/how-to-send-a-http-request-with-client-certificate-private-key-password-secret-in-python-3/
    # https://pythontic.com/ssl/sslcontext/load_cert_chain

    def _generate_tracking_id(self):
        """ Returns an uuid to be used as a unique tracking id"""
        return str(uuid.uuid4())

    def _generate_ctx(self):
        if self.ssl_protocol == "no_verify":
            return
        ctx = ssl.create_default_context()
        if self.ssl_protocol == "mutual":  # mTLS
            # Define the client certificate settings for https connection
            # https://www.techcoil.com/blog/how-to-send-a-http-request-with-client-certificate-private-key-password-secret-in-python-3/
            ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            ctx.load_cert_chain(certfile=self.ssl_certfile, keyfile=self.ssl_keyfile)
        elif self.ssl_protocol == "simple":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx

    @api.multi
    def _run_in(self):
        if self.protocol == "ipf":
            envelopes = []
            return envelopes
        else:
            super(EdiRoute, self)._run_in()

    @api.multi
    def _run_out(self, envelopes):
        if self.protocol == "ipf":
            if not (
                self.af_ipf_url
                or self.af_ipf_port
                or self.af_client_id
                or self.af_client_secret
                or self.af_environment
                or self.af_system_id
            ):
                raise Warning(
                    _("Please setup AF IPF Information")
                )  # this code should be unreachable.

            for envelope in envelopes:
                envelope_sent = True
                for msg in envelope.edi_message_ids:
                    try:
                        # send request to IPF based on message
                        self.send_request(msg)
                    except HTTPError as e:
                        formatted_error = f"HTTP error while sending message: {e.code} {e.reason}: {e.read()}"
                        msg.message_post(body=formatted_error)
                        _logger.warning(f"edi.message: {msg.id}: " + formatted_error)
                        msg.state = "canceled"
                        envelope_sent = False
                        break
                    except URLError as e:
                        formatted_error = f"URL error while sending message: {e.reason}"
                        msg.message_post(body=formatted_error)
                        _logger.warning(f"edi.message: {msg.id}: " + formatted_error)
                        msg.state = "canceled"
                        envelope_sent = False
                        break
                    except Exception as e:
                        # TODO: better error
                        msg.state = "canceled"
                        msg.message_post(body=_("ERROR!!!"))
                    else:
                        # Update that everything is A-OKAY.
                        msg.state = "sent"
                        msg.message_post(body=_("Message sent successfully."))

                if envelope_sent:
                    envelope.state = "sent"
                else:
                    envelope.state = "canceled"

        else:
            super(EdiRoute, self)._run_out(envelopes)

    def send_request(self, message):
        """ Method used for creating and sending REST request to IPF
        based on the information in the edi message and route. """

        def is_json(json_str):
            """ Checks if a str is a json or not. """
            try:
                return json.loads(json_str)
            # TODO: PEP 8: E722 do not use bare 'except'
            except:
                return False

        # Generate a unique tracking id
        message.name = af_tracking_id = self._generate_tracking_id()
        # Generate headers for our request
        get_headers = message._generate_headers(af_tracking_id)

        if message.body:
            _logger.debug("edi_route: message.body: %s" % message.body)
            if type(message.body) == bytes:
                body = message.body.decode("utf-8")
            else:
                body = message.body
            # A dict will start with "(" here.
            # Is there a prettier way to detect a dict here?
            if body[0] == "(":
                body = dict(ast.literal_eval(body))
                # The result of this line is never used. is this a bug?
                # Keeping the code but commenting it for now.
                # data_vals = json.loads(body.get("data").encode("utf-8"))
                data_vals = body.get("data")
                base_url = body.get("base_url")
                get_url = base_url.format(
                    url=self.af_ipf_url,
                    port=self.af_ipf_port,
                    client=self.af_client_id,
                    secret=self.af_client_secret,
                )
                get_headers["Content-Type"] = "application/json"
            elif type(message.body) == tuple:
                body = dict(body)
                data_vals = body.get("data")
                method = body.get("method", "GET")
                base_url = body.get("base_url")
                get_url = base_url.format(
                    url=self.af_ipf_url,
                    port=self.af_ipf_port,
                    client=self.af_client_id,
                    secret=self.af_client_secret,
                )
                get_headers["Content-Type"] = "application/json"
            elif is_json(body):
                body = json.loads(body.encode("utf-8"))
                data_vals = body.get("data")
                method = body.get("method", "GET")
                base_url = body.get("base_url")
                get_url = base_url.format(
                    url=self.af_ipf_url,
                    port=self.af_ipf_port,
                    client=self.af_client_id,
                    secret=self.af_client_secret,
                )
                get_headers["Content-Type"] = "application/json"

            # Else it should be a string
            # and begin with "{url}"
            else:
                get_url = body.format(
                    url=self.af_ipf_url,
                    port=self.af_ipf_port,
                    client=self.af_client_id,
                    secret=self.af_client_secret,
                )
                method = "GET"
                data_vals = False
        else:
            # TODO: throw error?
            return False

        _logger.debug("edi_route: get_url: %s" % get_url)
        _logger.debug("edi_route: data_vals: %s" % data_vals)
        _logger.debug("edi_route: get_headers: %s" % get_headers)
        _logger.debug("edi_route: method: %s" % method)
        # Build our request using url and headers
        # Request(url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None)
        if data_vals:
            # If we have data to send as a json, encode and attach it:
            data_vals = json.dumps(data_vals).encode("utf-8")
            req = request.Request(
                url=get_url, data=data_vals, headers=get_headers, method=method
            )
        else:
            req = request.Request(url=get_url, headers=get_headers, method=method)
        ctx = self._generate_ctx()
        # send GET and read result
        res_json = request.urlopen(req, context=ctx).read()

        # Convert json to python format: https://docs.python.org/3/library/json.html#json-to-py-table
        if res_json:
            res = json.loads(res_json)
        else:
            res = False

        _logger.debug("ipf_rest.get() message.edi_type: %s" % message.edi_type)

        # find the external id of our edi.message.type
        edi_type_ext_id = message.edi_type.get_external_id()[message.edi_type.id]
        # i.e. edi_type_ext_id = "edi_af_appointment.appointment_schedules"
        # make sure we found a match
        if edi_type_ext_id:
            # remove the module name from the string, and add an underscore
            mapped_function_name = "_" + edi_type_ext_id.split(".")[1]
            # i.e. mapped_function_name = "_appointment_schedules"
            # check that we have a function matching the name we got from external id
            if hasattr(self, mapped_function_name):
                # fetch the function
                mapped_function = getattr(self, mapped_function_name)
                # call the function
                mapped_function(message, res)
                # i.e. _appointment_schedules(message, res)
            else:
                # log that this is weird and move on
                _logger.warning(
                    f"No function found named '{mapped_function_name}' for edi.message.type '{edi_type_ext_id}'"
                )
                # TODO: throw error?
