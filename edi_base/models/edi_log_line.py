# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiLogLine(models.Model):
    _name = "edi.log.line"
    _description = "Represents log lines for an edi.log"
    _order = "create_date DESC"

    edi_log_id = fields.Many2one(comodel_name="edi.log", string="Log", required=True)
    name = fields.Char(string="Name", related="edi_log_id.name")
    log_message_type = fields.Char(string="Log Message Type")
    log_message = fields.Text(string="Log Message")
    log_message_state = fields.Selection(
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
