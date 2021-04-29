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
import json
import logging


_logger = logging.getLogger(__name__)


class EdiLog(models.Model):
    _inherit = "edi.log"

    af_ace_type = fields.Char(
        string="Meeting type", compute="_compute_log_data", store=True
    )
    af_ace_social_sec = fields.Char(
        string="Jobseeker", compute="_compute_log_data", store=True
    )
    af_ace_recid = fields.Char(
        string="Request Id", compute="_compute_log_data", store=True
    )
    af_ace_conid = fields.Char(
        string="Contact Id", compute="_compute_log_data", store=True
    )
    af_ace_mailuid = fields.Char(
        string="Email Uid", compute="_compute_log_data", store=True
    )

    def _compute_log_data(self):
        super(EdiLog, self)._compute_log_data()
        # complement data from super with ACE-specific data
        for record in self:
            sudo_message = record.message_id.sudo()
            if sudo_message.edi_type == self.env.ref(
                "edi_af_appointment.appointment_ace_wi"
            ):
                # ace_wi = self.env[sudo_message.model].browse(sudo_message.res_id).sudo()
                record.af_ace_type = (
                    sudo_message.model_record.appointment_id.type_id.name
                )
                record.af_ace_social_sec = (
                    sudo_message.model_record.appointment_id.partner_id.social_sec_nr
                )
                if record.state == "sent":
                    body = json.loads(sudo_message.body)
                    record.af_ace_recid = body.get("requestId")
                    record.af_ace_conid = body.get("contactId")
                    record.af_ace_mailuid = body.get("emailUid")
