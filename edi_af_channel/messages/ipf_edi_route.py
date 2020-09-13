# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
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
# edi_route_ipf - Interface to AF's integration platform: IPF

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
from urllib import request
from urllib.error import URLError, HTTPError
import json
import sys
import ssl
import uuid
import ast

import logging
_logger = logging.getLogger(__name__)


    def _as_channel(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']

        # Convert dict to tuple since a dict can't be encoded to bytes type
        body = tuple(sorted(schedule.items()))
        vals = {
            'name': "AS segment channel reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id.id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()   






        elif message.edi_type == message.env.ref('edi_af_channel.registration_channel'):
            self._as_channel(message, res)