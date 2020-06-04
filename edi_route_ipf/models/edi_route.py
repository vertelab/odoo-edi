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

import logging
_logger = logging.getLogger(__name__)

class _ipf(object):
    ''' Abstract class for communication-session. Use only subclasses.
        Subclasses are called by dispatcher function 'run'
    '''
    def __init__(self, host='localhost', username=None, password=None, port=None, environment=None, sys_id=None, debug=False):
        self.host = host
        self.username = username
        self.password = password
        self.debug = debug
        self.port = port
        self.environment = environment
        self.sys_id = sys_id

    def get(self, message):
        pass

    def post(self, message):
        pass

class ipf_rest(_ipf):
    ''' IPF: Class to communicate with IPF through REST '''

    def _generate_tracking_id(self, af_system_id, af_environment):
        tracking_number = datetime.now().strftime("%y%m%d%H%M%S")
        tracking_id = "%s-%s-%s" % (af_system_id.upper(), af_environment.upper(), tracking_number)
        return tracking_id

    def _generate_ctx(self, is_remote):
        ctx = ssl.create_default_context()
        if is_remote:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            pass # TODO: implement mTSL here?
        return ctx

    def _generate_headers(self, af_environment, af_system_id, af_tracking_id):
        get_headers = {
            'AF-Environment': af_environment,
            'AF-SystemId': af_system_id,
            'AF-TrackingId': af_tracking_id,
        }
        return get_headers

    def _schedules(self, message, res):
        _logger.warn("DAER: _run_out: schedules: %s" % "We got here!")
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']

        for comp_day in res:
            _logger.warn("DAER: _run_out: schedules: %s" % "looping per day")
            # assumes that there's only ever one competence
            type_id = message.env['calendar.appointment.type'].search([('ipf_id','=',comp_day.get('competence').get('id'))]).id
            for schedule in comp_day.get('schedules'):
                _logger.warn("DAER: _run_out: schedules: %s" % "looping per schedule")
                # Create messages from result
                # schedule['type_name'] = type_name
                schedule['type_id'] = type_id
                body = tuple(sorted(schedule.items()))
                # _logger.warn("DAER: _run_out: schedules: body: %s" % body)
                vals = {
                    'name': "Appointment schedule reply",
                    'body': body,
                    'edi_type': message.edi_type.id,
                    'route_type': message.route_type,
                }
                _logger.warn("DAER: _run_out: schedules: %s" % "Trying to create message")
                res_set |= message.env['edi.message'].create(vals)
                _logger.warn("DAER: _run_out: schedules: %s" % "Succesfully created message")

        _logger.warn("DAER: _run_out: schedules: %s" % "Trying to unpack")

        # unpack messages
        if res_set:
            res_set.unpack()
    
    def get(self, message):
        # Generate a unique tracking id
        af_tracking_id = self._generate_tracking_id(self.sys_id, self.environment)
        # Generate headers for our get
        get_headers = self._generate_headers(self.environment, self.sys_id, af_tracking_id)

        if message.body: 
            base_url = message.body.decode("utf-8")

            get_url = base_url.format(
                url = self.host,
                port = self.port,
                client = self.username,
                secret = self.password,
            )
        else:
            # TODO: throw error?
            pass

        _logger.warn("DAER: _run_out: get: get_url: %s" % get_url)

        # Build our request using url and headers
        # Request(url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None)
        req = request.Request(url=get_url, headers=get_headers)
        ctx = self._generate_ctx(True) # TODO: change to False
        # send GET and read result
        res_json = request.urlopen(req, context=ctx).read()
        # Convert json to python format: https://docs.python.org/3/library/json.html#json-to-py-table 
        res = json.loads(res_json)

        _logger.warn("DAER: _run_out: get: res: %s" % res)

        # get list of occasions from res
        if message.edi_type == message.env.ref('edi_af.appointment_schedules'):
            _logger.warn("DAER: _run_out: get: res = %s" % "schedules")
            self._schedules(message, res)
        # elif res.get('appointments', False):
        #     _appointments(res)
        elif not res:
            # No result given. Not sure how to handle.
            pass
        else:
            # TODO: throw error because we cant recognice the format of the result
            pass

class edi_route(models.Model):
    _inherit = 'edi.route' 
 
    ipf_debug = None

    # address
    af_ipf_url = fields.Char(string='IPF API URL',help="If you need help you shouldn't be changing this")
    af_ipf_port = fields.Char(string='IPF API port',help="If you need help you shouldn't be changing this")
    # id and secret
    af_client_id = fields.Char(string='Client Id',help="If you need help you shouldn't be changing this")
    af_client_secret = fields.Char(string='Client secret',help="If you need help you shouldn't be changing this")
    # headers
    af_environment = fields.Char(string='AF-Environment',help="If you need help you shouldn't be changing this")
    af_system_id = fields.Char(string='AF-SystemId',help="If you need help you shouldn't be changing this")
    # tracking_id is a unique id for each transaction. Not a good parameter to set.
    # af_tracking_id = fields.Char(string='AF-TrackingId',help="If you need help you shouldn't be changing this")
    
    protocol = fields.Selection(selection_add=[('ipf', 'IPF')])

    @api.multi
    def _run_in(self):
        # TODO: wait with this.
        if self.protocol == 'ipf':
            envelopes = []
            try:
                pass
            except Exception as e:
                self.log('error in ipf', sys.exc_info())
                _logger.error('error in ipf')
            else:
                try:
                    pass
                except Exception as e:
                    self.log('error in ipf', sys.exc_info())    
                    _logger.error('error in ipf READ')
                finally:
                    pass
            return envelopes
        else:
            super(edi_route, self)._run_in()

    @api.multi
    def _run_out(self, envelopes):
        if self.protocol == 'ipf':
            if not (self.af_ipf_url or self.af_ipf_port or self.client_id or self.client_secret or self.af_environment or self.af_system_id):
                raise Warning('Please setup AF IPF Information') # this code should be unreachable.

            # try:
            for envelope in envelopes:
                # try:
                envelope.state = 'sent'
                _logger.warn("DAER: _run_out: %s" % "Looping envelopes")
                for msg in envelope.edi_message_ids:
                    endpoint = ipf_rest(host=self.af_ipf_url, username=self.af_client_id, password=self.af_client_secret, port=self.af_ipf_port, environment=self.af_environment, sys_id=self.af_system_id)
                    _logger.warn("DAER: _run_out: %s" % "Trying to call IPF")
                    res_messages = endpoint.get(msg)
                    _logger.warn("DAER: _run_out: %s" % "Call to IPF completed, trying to read reply")
                    _logger.warn("DAER: _run_out: reply %s" % res_messages)
                    _logger.warn("DAER: _run_out: %s" % "updated status to sent")
                    msg.state = 'sent'
                    _logger.warn("DAER: _run_out: %s" % "updated status to sent")

                # except Exception as e:
                #     self.log('error when sending envelope %s' % envelope.name, sys.exc_info())    
                #     envelope.state = 'canceled'
                #     for msg in envelope.edi_message_ids:
                #         msg.state = 'canceled'
                #         _logger.warn("DAER: %s" % "Canceled message at edi_route_ipf _run_out")
            # except Exception as e:
            #     pass
        else:
            super(edi_route, self)._run_out(envelopes)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: