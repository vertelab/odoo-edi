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

{
    "name": "EDI AF Appointment",
    "version": "12.0.1.3.2",
    "category": "edi",
    "summary": "EDI AF Appointment - support for appointments ",
    "licence": "AGPL-3",
    'description': """
v12.0.0.1.0 - versions before good version control \n
v12.0.0.1.1 AFC-1536: Added support for calls to API with both pnr and customer_nr being sent at the same time. \n
v12.0.0.2.0 AFC-1905: Added option to prioritise the order in which WI are sent to Telia ACE in. \n
v12.0.0.2.1 AFC-1805: Duration of PDM occasions now handled differently. \n
v12.0.0.2.2 AFC-1715: Added support for new appointment types. \n
v12.0.1.0.0 AFC-1766: Major overhaul of how the module works. \n
v12.0.1.1.0 AFC-1767: Implemented a special view and menuitem for calendar_af users to monitor ACE messages. \n
v12.0.1.2.0 AFC-2298: Fixed edi.log access rights. Fixed menu locations and access rights. \n
v12.0.1.3.0 AFC-2169: Can now book meetings on non-existing jobseekers. \n
v12.0.1.3.1 AFC-2526: Changed Occasions duration to seconds instead of minutes. \n
v12.0.1.3.2 AFC-2306: Removed '-' from phonenumber in workitem. \n
""",
    "author": "Vertel AB",
    "website": "http://www.vertel.se",
    "depends": [
        "edi_route",
        "calendar_af",
        "edi_route_ipf",
        "af_security",
    ],
    "external_dependencies": {},
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/edi_route_data.xml",
        "data/edi.ace_queue.csv",
        "data/edi.ace_errand.csv",
        "views/edi_af_appointment_views.xml",
        "views/edi_log_ace_view.xml",
        "data/scheduled_meeting_reminder.xml",
    ],
    "application": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
