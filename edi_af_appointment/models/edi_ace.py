# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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


class EdiAceWorkitem(models.Model):
    _name = "edi.ace_workitem"

    name = fields.Char(string="Name")
    text = fields.Char(string="Text")
    appointment_id = fields.Many2one(
        comodel_name="calendar.appointment", string="Appointment"
    )
    queue = fields.Many2one(comodel_name="edi.ace_queue", string="ACE queue")
    errand = fields.Many2one(comodel_name="edi.ace_errand", string="ACE errand")


class EdiAceQueue(models.Model):
    _name = "edi.ace_queue"

    name = fields.Char(string="Name")
    app_type_id = fields.Many2one(
        comodel_name="calendar.appointment.type", string="Meeting type"
    )


class EdiAceErrand(models.Model):
    _name = "edi.ace_errand"

    name = fields.Char(string="Name", size=25, trim=True)
    app_type_id = fields.Many2one(
        comodel_name="calendar.appointment.type", string="Meeting type"
    )
    right_type = fields.Selection(
        string="Right Type",
        selection=[("", "None"), ("STARK", "Stark"), ("MYCKET_STARK", "Mycket Stark")],
    )
    code = fields.Char(
        string="Errand Code",
        size=3,
        trim=True,
    )
    reason_code = fields.Char(string="Reason Code", size=2)
    interval = fields.Selection(
        selection=[
            ("1", "1 day"),
            ("7", "1 week"),
            ("14", "2 weeks"),
            ("30", "30 days"),
            ("60", "60 days"),
            ("100", "100 days"),
            ("365", "a Year"),
        ],
        string="Interval",
        default="1",
    )
    client_responsible = fields.Boolean(
        string="Client Responsible",
        help="Change current user to be responsible for this client, and get permanent rights that goes with it",
    )
    office_code = fields.Char(string="Office code")
    priority = fields.Integer(string='Send priority')

    @api.model
    def escalate_jobseeker_access(self, partner, errand_id, user):
        _logger.debug("escalate_jobseeker_access: start")
        # find meeting_type from errand
        errand = self.env["edi.ace_errand"].sudo().search([("code", "=", errand_id)])
        _logger.debug("escalate_jobseeker_access: errand.code %s" % errand.code)
        _logger.debug(
            "escalate_jobseeker_access: errand.interval: %s type: %s"
            % (errand.interval, type(errand.interval))
        )
        if errand.client_responsible:
            # change user_id
            vals = {"user_id": user.id}
            partner.with_context(office_code=errand.office_code).write(vals)
        # request partner access for user
        res = partner._grant_jobseeker_access(
            access_type=errand.right_type,
            reason_code=errand.reason_code,
            reason=errand.name,
            interval=int(errand.interval),
            user=user,
        )
        fail_list = res.get("body").get("nyckelMisslyckadLista")
        if not fail_list:
            fail_list = [
                {"felKod": 250, "felOrsak": "OK"},
            ]
        fail_dict = fail_list[0]
        res = fail_dict.get("felKod"), fail_dict.get("felOrsak")
        return res


class CalendarAppointment(models.Model):
    _inherit = "calendar.appointment"

    ace_priority = fields.Integer(string='ACE priority', related='type_id.ace_errand_id.priority')


class CalendarAppointmentType(models.Model):
    _inherit = "calendar.appointment.type"

    ace_queue_id = fields.One2many(
        comodel_name="edi.ace_queue", inverse_name="app_type_id", string="ACE queue"
    )
    ace_errand_id = fields.One2many(
        comodel_name="edi.ace_errand", inverse_name="app_type_id", string="ACE errand"
    )
