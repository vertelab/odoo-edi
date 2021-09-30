# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
from .edi_error import EDIUnkownMessageError

_logger = logging.getLogger(__name__)


class EdiRoute(models.Model):
    """A route responsible for communication in a certain protocol"""

    _name = "edi.route"
    _description = "EDI Route"

    name = fields.Char(string="Name", required=True)
    is_active = fields.Boolean(string="Active", default=True)
    protocol = fields.Selection(string='Protocol', selection=[])
    frequency = fields.Integer(
        string="Frequency", help="Number of minutes between each execution."
    )
    next_run = fields.Datetime(string="Next run")
    envelope_ids = fields.One2many(
        comodel_name="edi.envelope", inverse_name="route_id", string="Envelopes"
    )
    envelope_count = fields.Integer(compute="_envelope_count", string="no. envelopes")
    log_count = fields.Integer(compute="_log_count", string="no. logs")

    def _envelope_count(self):
        for rec in self:
            rec.envelope_count = self.env["edi.envelope"].search_count(
                [("route_id", "=", rec.id)]
            )

    def _log_count(self):
        for rec in self:
            rec.log_count = self.env["edi.log"].search_count(
                [("message_id.route_id", "=", rec.id)]
            )

    def check_connection(self):
        """Check connection"""
        # TODO implement
        return False

    def route_is_active_button(self):
        for rec in self:
            rec.is_active = not rec.is_active

    def run_in(self):
        pass

    def run_out(self):
        """Process messages on route"""
        for rec in self:
            envelopes = rec.envelope_ids.filtered(lambda r: r.state in ["created", "processing"])
            for envelope in envelopes:
                envelope.send()

        # envelopes = self.envelope_ids.filtered(lambda r: r.state in ["created", "processing"])
        # envelopes.write({"state": "processing"})
        # for envelope in envelopes:
        #     # find the external id of our edi.message.type
        #     edi_type_ext_id = envelope.type_id.get_external_id()[envelope.type_id.id]
        #     # i.e. edi_type_ext_id = "???.???"
        #     # make sure we found a match
        #     if edi_type_ext_id:
        #         mapped_function_name = "_" + edi_type_ext_id.replace(".", "_")
        #         # i.e. mapped_function_name = "???"
        #         # check that we have a function matching the name we got from external id
        #         if hasattr(self, mapped_function_name):
        #             # fetch the function
        #             mapped_function = getattr(self, mapped_function_name)
        #             # call the function
        #             mapped_function(envelope)
        #             # i.e. ????(envelope)
        #         else:
        #             error_msg = _(
        #                 "No function found named '{mapped_function_name}' for edi.type '{edi_type_ext_id}'"
        #             )
        #             raise EDIUnkownMessageError(
        #                 error_msg.format(
        #                     mapped_function_name=mapped_function_name,
        #                     edi_type_ext_id=edi_type_ext_id,
        #                 )
        #             )
