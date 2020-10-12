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

class _ipf(object):
    ''' Abstract class for communication-session. Use only subclasses.
        Subclasses are called by dispatcher function 'run'
    '''
    def __init__(self, host='localhost', username=None, password=None, port=None, environment=None, sys_id=None, authorization=None, debug=False, ssl_protocol=None, ssl_certfile=None, ssl_keyfile=None):
        self.host = host
        self.username = username
        self.password = password
        self.debug = debug
        self.port = port
        self.environment = environment
        self.sys_id = sys_id
        self.authorization = authorization
        self.ssl_protocol = ssl_protocol
        self.ssl_certfile = ssl_certfile
        self.ssl_keyfile = ssl_keyfile

    def get(self, message):
        pass

    def post(self, message):
        pass

class ipf_rest(_ipf):
    ''' IPF: Class to communicate with IPF through REST '''

    def _generate_tracking_id(self):
        """ Returns an uuid as an unique tracking id"""
        return str(uuid.uuid4())

    def _generate_ctx(self):
        if self.ssl_protocol == 'no_verify':
            return
        ctx = ssl.create_default_context()
        if self.ssl_protocol == 'mutual': # mTLS
            # Define the client certificate settings for https connection
            # https://www.techcoil.com/blog/how-to-send-a-http-request-with-client-certificate-private-key-password-secret-in-python-3/
            ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            ctx.load_cert_chain(certfile=self.ssl_certfile, keyfile=self.ssl_keyfile)
        elif self.ssl_protocol == 'simple':
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        #else: # route.ssl_protocol == 'no_verifiaction';
        return ctx

    def _generate_headers(self, af_environment, af_system_id, af_tracking_id):
        get_headers = {
            'AF-Environment': af_environment,
            'AF-SystemId': af_system_id,
            'AF-TrackingId': af_tracking_id,
            'AF-EndUserId': 'AFCRM',
        }
        return get_headers

    def _schedules(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']

        for comp_day in res:
            # assumes that there's only ever one competence
            type_id = message.env['calendar.appointment.type'].search(
                [('ipf_id','=',comp_day.get('competence').get('id'))]).id
            for schedule in comp_day.get('schedules'):
                # Create messages from result
                schedule['type_id'] = type_id
                # Convert dict to tuple since a dict can't be encoded to bytes type
                body = tuple(sorted(schedule.items()))
                vals = {
                    'name': "Appointment schedule reply",
                    'body': body,
                    'edi_type': message.edi_type.id,
                    'route_type': message.route_type,
                }
                res_set |= message.env['edi.message'].create(vals)

        # unpack messages
        if res_set:
            res_set.unpack()

        message.model_record.inactivate()

    def _as_office(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']
        path = message.body
        path_arr = path.split('/')
        customer_id = path_arr[4].split('?')[0] 
        res.update({'sokande_id': customer_id})
        body = json.dumps(res)
        vals = {
            'name': "AS office reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()


    def _officer(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']
        body = json.dumps(res)
        vals = {
            'name': "AS office reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()
          
    def _as_channel(self, message, res):
        res_set = message.env['edi.message']

        patharray = message.body.split('/')   #skapa array av värden
        res.update({'SokandeId':int(patharray[4].split('?', 1)[0])})        
        body = json.dumps(res)        
        vals = {
            'name': "AS segment reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()

    def _as_krom_postcode(self, message, res):
        res_set = message.env['edi.message']
        body = json.dumps(res)
        vals = {
            'name': "AS krom postcode reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()

    def _as_notes(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']

        body = tuple(sorted(res))
        vals = {
            'name': "AS Note reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id.id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()

    def _af_facility(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']
        body = json.dumps(res)
        vals = { #cannot get past this line
            'name': "AF Facility reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id,
            'route_type': message.route_type,
        }
        
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()
    
    def _ag_org(self, message, res):
        # Create calendar.schedule from res
        # res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        res_set = message.env['edi.message']

        body = tuple(sorted(res))
        vals = {
            'name': "AS Org reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id.id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        # unpack messages
        res_message.unpack()

    def _ace_wi(self, message, res):
        # Why does these not update?
        message.state = "received"
        message.envelope_id.state = "received"
        
        ace_wi = message.env['edi.ace_workitem'].search([('id', '=', message.res_id)])
        app = message.env['calendar.appointment'].search([('id', '=', ace_wi.appointment_id.id)])
        app.state = 'done'

    def _as_contact(self, message, res):
        # Why does these not update?
        message.state = "received"
        message.envelope_id.state = "received"

    def _rask_get_all(self, message, res):
        # Get the answer from the call to AIS-F RASK
        res_set = message.env['edi.message']

        # TODO: continue here... i think the structure of res somehow breaks this conversion.
        body = json.dumps(res)
        vals = {
            'name': "RASK get all reply",
            'body': body,
            'edi_type': message.edi_type.id,
            'res_id': message.res_id,
            'route_type': message.route_type,
        }
        res_message = message.env['edi.message'].create(vals)
        res_message.unpack()

    def get(self, message):
        # Generate a unique tracking id
        message.name = af_tracking_id = self._generate_tracking_id()
        # Generate headers for our get
        get_headers = self._generate_headers(self.environment, self.sys_id, af_tracking_id)

        if message.body:
            if type(message.body) == bytes :
                body = message.body.decode("utf-8")
            else:
                body = message.body
            # A dict will start with "(" here.
            # Is there a prettier way to detect a dict here? 
            if body[0] == "(":
                body = dict(ast.literal_eval(body))
                # data_vals = json.loads(body.get('data').encode("utf-8"))
                data_vals = body.get('data')
                base_url = body.get('base_url')
                get_url = base_url.format(
                    url = self.host,
                    port = self.port,
                    client = self.username,
                    secret = self.password,
                )
                get_headers['Content-Type'] = 'application/json'
            elif type(message.body) == tuple:
                body = dict(body)
                # data_vals = json.loads(body.get('data').encode("utf-8"))
                data_vals = body.get('data')
                base_url = body.get('base_url')
                get_url = base_url.format(
                    url = self.host,
                    port = self.port,
                    client = self.username,
                    secret = self.password,
                )
                get_headers['Content-Type'] = 'application/json'

            # Else it should be a string
            # and begin with "{url}"
            else:
                get_url = body.format(
                    url = self.host,
                    port = self.port,
                    client = self.username,
                    secret = self.password,
                )
                data_vals = False
        else:
            # TODO: throw error?
            pass

        if message.edi_type == message.env.ref('edi_af_as_notes.edi_af_as_notes_post', raise_if_not_found=False):
            get_headers.update({'Authorization': self.authorization, 'PISA_ID': data_vals.get('ansvarSignatur')}) #Authorization med given username+password och PISA_ID med antingen sys eller handläggares signatur
        elif message.edi_type == message.env.ref('edi_af_as.asok_office', raise_if_not_found=False) or message.edi_type == message.env.ref('edi_af_as.asok_contact', raise_if_not_found=False):
            get_headers.update({'Authorization': self.authorization, 'PISA_ID': '*sys*'}) #X-JWT-Assertion eller alternativt Authorization med given data och PISA_ID med antingen sys eller handläggares signatur
        elif message.edi_type == message.env.ref('edi_af_channel.registration_channel', raise_if_not_found=False):
            get_headers.update({'Authorization': self.authorization, 'PISA_ID': '*sys*'}) #X-JWT-Assertion eller alternativt Authorization med given data och PISA_ID med antingen sys eller handläggares signatur
        elif message.edi_type == message.env.ref('edi_af_aisf_rask.rask_get_all', raise_if_not_found=False):
            get_headers.update({'PISA_ID': '*sys*'}) #HTTP-headern med dess värde krävs för AS med skyddad identitet

        # Build our request using url and headers
        # Request(url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None)
        if data_vals:
            # If we have data to send as a json, encode and attach it:
            data_vals = json.dumps(data_vals).encode("utf-8")
            req = request.Request(url=get_url, data=data_vals, headers=get_headers)
        else:
            req = request.Request(url=get_url, headers=get_headers)
        ctx = self._generate_ctx() # TODO: change to False
        # send GET and read result
        res_json = request.urlopen(req, context=ctx).read()
        # Convert json to python format: https://docs.python.org/3/library/json.html#json-to-py-table 
        res = json.loads(res_json)
        # get list of occasions from res



        _logger.info("ipf_rest.get() message.edi_type: %s" % message.edi_type)
        if message.edi_type == message.env.ref('edi_af_appointment.appointment_schedules', raise_if_not_found=False):
            self._schedules(message, res)
        elif message.edi_type == message.env.ref('edi_af_appointment.appointment_ace_wi', raise_if_not_found=False):
            self._ace_wi(message, res)
        elif message.edi_type == message.env.ref('edi_af_facility.office_campus', raise_if_not_found=False):
            self._af_facility(message, res)
        elif message.edi_type == message.env.ref('edi_af_as.asok_office', raise_if_not_found=False):
            self._rask_get_all(message, res)
        elif message.edi_type == message.env.ref('edi_af_aisf_rask.rask_get_all', raise_if_not_found=False):
            self._rask_get_all(message, res)
        elif message.edi_type == message.env.ref('edi_af_as.asok_contact', raise_if_not_found=False):
            self._as_contact(message, res)
        elif message.edi_type == message.env.ref('edi_af_channel.registration_channel', raise_if_not_found=False):
            self._as_channel(message, res)
        elif message.edi_type == message.env.ref('edi_af_krom_postcode.asok_postcode', raise_if_not_found=False):
            self._as_krom_postcode(message, res)
        elif message.edi_type == message.env.ref('edi_af_channel.registration_channel', raise_if_not_found=False):
            self._as_office(message, res)
        elif message.edi_type == message.env.ref('edi_af_officer.get_officer'):
            self._officer(message, res)
        elif message.edi_type == message.env.ref('edi_af_as_notes.edi_af_as_notes_post', raise_if_not_found=False):
            self._as_notes(message, res)
        elif message.edi_type == message.env.ref('edi_af_ag.ag_organisation', raise_if_not_found=False):
            self._ag_org(message, res)
        elif not res:
            # No result given. Not sure how to handle.
            pass
        else:
            # TODO: throw error because we cant recognize the format of the result
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
    af_authorization_header = fields.Char(string='AF-Authorization header',help="If you need help you shouldn't be changing this")

    # tracking_id is a unique id for each transaction. Not a good parameter to set.
    # af_tracking_id = fields.Char(string='AF-TrackingId',help="If you need help you shouldn't be changing this")
    
    protocol = fields.Selection(selection_add=[('ipf', 'IPF')])
    ssl_protocol = fields.Selection(selection=[('no_verify','No verification'),('simple','Simple verification'),('mutual','Mutual verification (mTLS)')],string='SSL-Protocol')
    ssl_certfile = fields.Char(string='SSL Cert File Path',help="Path of the X.509 certificate file in PEM(Privacy Enhanced Email) format")
    ssl_keyfile = fields.Char(string='SSL Key File Path',help="Path of the X.509 private key of the certificate")
    # https://www.techcoil.com/blog/how-to-send-a-http-request-with-client-certificate-private-key-password-secret-in-python-3/
    # https://pythontic.com/ssl/sslcontext/load_cert_chain

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
            if not (
                    self.af_ipf_url or self.af_ipf_port or self.af_client_id or self.af_client_secret or self.af_environment or self.af_system_id):
                raise Warning('Please setup AF IPF Information') # this code should be unreachable.

            try:
                for envelope in envelopes:
                    for msg in envelope.edi_message_ids:
                        endpoint = ipf_rest(
                                    host=self.af_ipf_url, 
                                    username=self.af_client_id, 
                                    password=self.af_client_secret, 
                                    port=self.af_ipf_port, 
                                    environment=self.af_environment, 
                                    sys_id=self.af_system_id, 
                                    authorization=self.af_authorization_header,
                                    ssl_protocol=self.ssl_protocol,
                                    ssl_certfile=self.ssl_certfile,
                                    ssl_keyfile=self.ssl_keyfile,
                                    )
                        res_messages = endpoint.get(msg)
                        msg.state = 'sent'
                    
                    envelope.state = 'sent'

            except Exception as e:
                self.log('error when sending envelope %s' % envelope.name, sys.exc_info())    
                envelope.state = 'canceled'
                for msg in envelope.edi_message_ids:
                    msg.state = 'canceled'

        else:
            super(edi_route, self)._run_out(envelopes)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
