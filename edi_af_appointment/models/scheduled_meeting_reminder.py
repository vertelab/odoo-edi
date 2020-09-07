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
import datetime


class ScheduledMeeting(models.Model):
    _inherit = 'calendar.appointment'

    def send_out_message(self):
        # self.env['calendar.appointment'].search([('state', '=', 'confirmed')])
        appointment_ids = self.env['calendar.appointment'].search([])
        for record in appointment_ids:
            before_start_time = record.start - datetime.timedelta(minutes=10)
            if before_start_time.strftime('%H:%M') == datetime.datetime.now().strftime('%H:%M'):
                pass
                #TODO: fix this...
                # template = self.env.ref('edi_af_appointment.email_template_calendar_schedule_reminder')
                # self.env['mail.template'].browse(template.id).send_mail(record.id, force_send=True)

                text = "Test-text"
                app = record
                queue = self.env.ref('edi_ace_queue.as_uppfstomw')
                errand = app.type_id

                vals = {
                'name': "IPF request",
                'text': text,
                'appointment_id': app.id,
                'queue': queue.id,
                }
                ace_wi = self.env['edi.ace_workitem'].create(vals)

                vals = {
                'name': 'ACE TEST!',
                'edi_type': self.env.ref('edi_af_appointment.appointment_ace_wi').id,
                'model': ace_wi._name,
                'res_id': ace_wi.id,
                'route_id': 2,
                'route_type': 'edi_af_ace_wi',
                }
                msg = self.env['edi.message'].create(vals)
                msg.pack()