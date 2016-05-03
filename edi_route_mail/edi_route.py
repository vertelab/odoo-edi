# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


import time
import datetime
import fnmatch
import zipfile
import base64

import logging
_logger = logging.getLogger(__name__)


            
class edi_route(models.Model):
    _inherit = 'edi.route' 
    _inherits = {"mail.alias": "alias_id"}
    
    alias_id = fields.Many2one(comodel_name='mail.alias', string='Alias', ondelete="restrict", required=True,
                                    help="Internal email associated with this route. Incoming emails are automatically synchronized"
                                         "with messagesd.")
    alias_model = fields.Char(String="Alias Model",default='edi.message')
    mail_address = fields.Char(string="Mail Address",required=True)
    mail_debug = fields.Boolean(string="Debug")
    route_type = fields.Selection(selection_add=[('mail','Mail')])
    
    
    @api.one
    def run(self):
        super(edi_route, self).run()
        _logger.info('run [%s:%s]' % (self.name,self.route_type))
        envelops = []
        if self.route_type == 'ftp':
            pass
        elif self.route_type == 'mail':
            if self.mail_debug:
                _logger.debug('sftp host=%s  username=%s password=%s' % (self.ftp_host,self.ftp_user,self.ftp_password))
            try:
                server =  sftp(host=self.ftp_host,username=self.ftp_user,password=self.ftp_password,debug=self.ftp_debug)
                server.connect()
            except Exception as e:
                if self.ftp_debug:
                    self.log('error in sftp %s' % e)                
                _logger.error('error in sftp %s' % e)
            else:
                try:
                    if self.ftp_debug:
                        _logger.info('info list %s' % server.list_files(path=self.ftp_directory,pattern=self.ftp_pattern))
                    for f in server.list_files(path=self.ftp_directory,pattern=self.ftp_pattern):
                        envelops.append(self.env['edi.envelope'].create({'name': f, 'body': base64.encodestring(server.get_file(f)), 'route_id': self.id}))                
                        # self.rm(f)
                except Exception as e:
                    if self.ftp_debug:
                        self.log('error in sftp %s' % e)                
                    _logger.error('error in sftp READ %s' % e)             
                finally:
                    server.disconnect()
            log = 'sftp host=%s  username=%s password=%s\nNbr envelops %s\n%s' % (self.ftp_host,self.ftp_user,self.ftp_password,len(envelops),','.join([e.name for e in envelops]))
            _logger.info(log)
            if self.ftp_debug:
                self.log(log)
                    

    @api.one
    def get_file(self):
        _logger.info('get_file [%s:%s]' % (self.name,self.route_type))
        if self.route_type == 'ftp':
            pass
        elif self.route_type == 'sftp':
           pass
            
        else:
            super(edi_route, self).check_connection()        
    @api.one
    def put_file(self,file):
        _logger.info('put_file [%s:%s]' % (self.name,self.route_type))
        if self.route_type == 'ftp':
            pass
        elif self.route_type == 'sftp':
            pass
        else:
            super(edi_route, self).check_connection()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
