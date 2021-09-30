# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiLog(models.Model):
    """This model is implemented in order to be able to present data
    about EDI messages and their status to users in the system without
    giving them access to sensitive data on edi.message."""

    _name = "edi.log"
    _description = "Logs events for an edi.message"
    _order = "create_date DESC"

    message_id = fields.Many2one(
        comodel_name="edi.message", string="Message", required=True, readonly=True
    )
    name = fields.Char(string="Name")
    route = fields.Char(string="Route")
    message_type = fields.Char(string="Message type")
    state = fields.Selection(
        [
            ("created", "Created"),
            ("processing", "Processing"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("done", "Done"),
            ("canceled", "Canceled"),
        ],
        default="created",
    )
    log_line_ids = fields.One2many(
        comodel_name="edi.log.line", inverse_name="edi_log_id", string="Log lines"
    )
