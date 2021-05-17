# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
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
import logging


_logger = logging.getLogger(__name__)


class EdiLog(models.Model):
    """This model is implemented in order to be able to present data
    about EDI messages and their status to users in the system without
    giving them access to sensitive data on edi.message."""

    _name = "edi.log"
    _inherit = ["mail.thread"]
    _description = "Log of EDI message"
    _order = "create_date DESC"

    name = fields.Char(string="Name", compute="_compute_log_data", store=True)
    message_id = fields.Many2one(
        comodel_name="edi.message", string="Message", required=True
    )
    message_type = fields.Char(
        string="Message type", compute="_compute_log_data", store=True
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("progress", "Progress"),
            ("sent", "Sent"),
            ("received", "Received"),
            ("canceled", "Canceled"),
        ],
        compute="_compute_log_data",
        store=True,
    )

    @api.depends("message_id.state")
    def _compute_log_data(self):
        for record in self:
            sudo_message = record.message_id.sudo()
            record.name = sudo_message.name
            record.message_type = sudo_message.edi_type.name
            record.state = sudo_message.state
