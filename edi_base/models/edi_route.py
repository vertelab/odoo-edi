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
    # TODO: rename protocol, remove?
    # protocol = fields.Selection(string="Protocol", selection=[])
    frequency = fields.Integer(
        string="Frequency", help="Number of minutes between each execution."
    )
    next_run = fields.Datetime(string="Next run")
    envelope_ids = fields.One2many(
        comodel_name="edi.envelope", inverse_name="route_id", string="Envelopes"
    )
    envelope_count = fields.Integer(compute="_envelope_count", string="no. envelopes")
    log_count = fields.Integer(compute="_log_count", string="no. logs")
    process_id = fields.Many2one("edi.process", string="Process")

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
        return False

    def route_is_active_button(self):
        for rec in self:
            rec.is_active = not rec.is_active

    def _run_in(self):
        """Find & process incoming messages for route"""
        pass

    def run_in(self):
        try:
            self._run_in()
        except Exception as e:
            pass

    def _run_out(self, envelopes):
        """Process outgoing messages on route"""
        for envelope in envelopes:
            envelope.fold()
            envelope.send()

    def run_out(self):
        try:
            self._run_out(self.envelope_ids)
        except Exception as e:
            pass

    def run(self):
        self._run_in()
        self._run_out(self.envelope_ids)


class EdiProcess(models.Model):
    _name = "edi.process"
    _description = "EDI Process"

    name = fields.Char(string="Name")


class EdiProtocol(models.Model):
    _name = "edi.protocol"
    _description = "EDI Protocol"

    name = fields.Char(string="Name")
