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
from odoo.exceptions import Warning

import json
import sys

import logging
_logger = logging.getLogger(__name__)

class edi_route(models.Model):
    _inherit = 'edi.route' 
    # https://exchangeratesapi.io/
    protocol = fields.Selection(selection_add=[('ecb_rest', 'ECB Rest')])
    # Define base url
    # ex: https://ipfapi.arbetsformedlingen.se:443/appointments/v1/bookable-occasions?appointment_type=1&appointment_channel=SPD&from_date=2020-03-20&to_date=2020-03-21&client_id=da03472cd17e4ce4bb2d017156db7156&client_secret=B4BC32F21a314Cb9B48877989Cc1e3b8
    base_url = "{url}:{port}/{path}?client_id={client}&client_secret={secret}&from_date={from_date_str}&to_date={to_date_str}&appointment_channel={appointment_channel_str}&appointment_type={appointment_type_str}{max_depth_str}{appointment_length_str}{location_code_str}{profession_id_str}"

    
    @api.multi
    def _run_in(self):
        if self.protocol == 'ecb_rest':
            envelopes = []

            if self.ftp_debug:
                _logger.debug('ipf host=%s  username=%s password=%s' % (self.ftp_host, self.ftp_user, self.ftp_password))

            try:
                server =  ipf(host=self.ftp_host, username=self.ftp_user, password=self.ftp_password, debug=self.ftp_debug)
                server.connect()
            except Exception as e:
                self.log('error in ipf', sys.exc_info())                   
                _logger.error('error in ipf')
            else:
                try:
                    server.set_cwd(self.ftp_directory_in or '.')
                    f_list = server.list_files(pattern=self.ftp_pattern or '*')

                    if self.ftp_debug:
                        _logger.info('info list %s' % f_list)

                    for f in f_list:
                        envelopes.append(self.env['edi.envelope'].create({
                            'name': f,
                            'body': base64.encodestring(server.get_file(f)),
                            'route_id': self.id,
                            'route_type': self.route_type
                        }))
                        server.rm(f)
                except Exception as e:
                    self.log('error in ipf', sys.exc_info())    
                    _logger.error('error in ipf READ')
                finally:
                    server.disconnect()

            log = 'ipf host=%s  username=%s password=%s\nNbr envelopes %s\n%s' % (self.ftp_host, self.ftp_user, self.ftp_password, len(envelopes), ','.join([e.name for e in envelopes]))
            _logger.info(log)

            if self.ftp_debug:
                self.log(log)

            return envelopes
        else:
            super(edi_route, self)._run_in()
    
    @api.multi
    def _run_out(self, envelopes):
        _logger.debug('edi_route._run_out (ipf): %s' % envelopes)
        if self.protocol == 'ipf':
            if not (self.af_url or self.af_port or self.client_id or self.client_secret or self.af_environment or self.af_system_id):
                raise Warning('Please setup AF IPF Information')

            if self.ipf_debug:
                _logger.debug('ipf - af_ipf_url=%s af_ipf_port=%s af_client_id=%s af_client_secret=%s af_environment=%s af_system_id=%s' % 
                                (self.af_ipf_url, self.af_ipf_port, self.af_client_id, self.af_client_secret, self.af_environment, self.af_system_id))

            try:
                for envelope in envelopes:
                    try:
                        for msg in envelope.edi_message_ids:
                            # Call rest API here

                            url_params = msg.body

                             # Insert values into base_url
                            get_url = base_url.format(
                                url = af_url, # https://ipfapi.arbetsformedlingen.se
                                port = af_port, # 443
                                path = msg.edi_type.type_target, #"appointments/v1/bookable-occasions", # TODO: remove hardcoding?
                                client = client_id, # check in anypoint for example
                                secret = client_secret, # check in anypoint for example
                                params = url_params, # type specific params
                            )
                            # Logg stuff to see what I get
                            _logger.info('url=%s' % (get_url))
                            msg.state = 'sent'

                    except Exception as e:
                        self.log('error when sending envelope %s' % envelope.name, sys.exc_info())    
                        envelope.state = 'canceled'
                        for msg in envelope.edi_message_ids:
                            msg.state = 'canceled'
            except Exception as e:
                if self.ipf_debug:
                    self.log('error in ipf', sys.exc_info())                   
                _logger.error('error in ipf')

            log = 'ipf  - log something useful %s' % ('here')
            _logger.info(log)
            if self.ipf_debug:
                self.log(log)
        else:
            super(edi_route, self)._run_out(envelopes)


class edi_envelope(models.Model):
    _inherit = 'edi.envelope'


    # ~ @api.model
    # ~ def _route_default(self):
        # ~ route = self.env['edi.route'].browse(self._context.get('default_route_id'))
        # ~ if route:
            # ~ return route.id
        # ~ else:
            # ~ return self.env['edi.route'].search([])[0]
    # ~ route_id = fields.Many2one(comodel_name='edi.route',required=True,default=_route_default)
    
    route_type = fields.Selection(selection_add=[('ecb_rest','ECB Rest')])

    @api.one
    def _split(self):
        if self.route_type == 'ecb_rest':
            msg = self.env['edi.message'].create({
                'name': 'plain',
                'envelope_id': self.id,
                'body': self.body,
                'route_type': self.route_type,
                'sender': self.sender,
                'recipient': self.recipient,
                #~ 'consignor_id': sender.id,
                #~ 'consignee_id': recipient.id,
            })
            msg.unpack()
        self.envelope_opened()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: