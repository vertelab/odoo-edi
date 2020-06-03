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

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

import os
import sys
import posixpath
import time
import datetime
import glob
import shutil
import fnmatch
import zipfile
import ftplib
import base64
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class _comsession(object):
    ''' Abstract class for communication-session. Use only subclasses.
        Subclasses are called by dispatcher function 'run'
    '''
    def __init__(self, host='localhost', username=None, password=None, port=None, debug=False):
        self.host = host
        self.username = username
        self.password = password
        self.debug = debug
        self.port = port
        self.session = None
        self.transport = None

    def connect(self):
        pass

    def disconnect(self):
        pass

    def set_cwd(self,path):
        self.session.chdir('.') # getcwd does not work without this chdir first!
        wd = self.session.getcwd()
        if path:
            wd = posixpath.normpath(posixpath.join(wd,path))
            try:
                self.session.chdir(wd)
            except:
                self.session.mkdir(wd)
                self.session.chdir(wd)
        return wd
    
    def convertcodecformime(codec_in):
        convertdict = {
            'ascii' : 'us-ascii',
            'unoa' : 'us-ascii',
            'unob' : 'us-ascii',
            'unoc' : 'iso-8859-1',
            }
        codec_in = codec_in.lower().replace('_','-')
        return convertdict.get(codec_in,codec_in)

class ftp(_comsession):
    def connect(self):
        self.session = ftplib.FTP()
        self.session.set_debuglevel(2 if self.debug else 0)   #set debug level (0=no, 1=medium, 2=full debug)
        self.session.set_pasv(not self.ftpactive) #active or passive ftp
        self.session.connect(host=self.host,port=self.port or 21)
        self.session.login(user=self.username,passwd=self.password,acct=self.ftpaccount)
        self.set_cwd()

    def set_cwd(self,path):
        self.session.chdir('.') # getcwd does not work without this chdir first!
        wd = self.session.pwd()
        if path:
            wd = posixpath.normpath(posixpath.join(wd,path))
            try:
                self.session.cwd(wd)
            except:
                self.session.mkd(wd)
                self.session.cwd(wd)
        return wd


    def incommunicate(self):
        ''' do ftp: receive files. To be used via receive-dispatcher.
            each to be imported file is transaction.
            each imported file is transaction.
        '''
        startdatetime = datetime.datetime.now()
        files = []
        try:            #some ftp servers give errors when directory is empty; catch these errors here
            files = self.session.nlst()
        except (ftplib.error_perm,ftplib.error_temp) as msg:
            if unicode(msg)[:3] not in [u'550',u'450']:
                raise

        lijst = fnmatch.filter(files,self.channeldict['filename'])
        remove_ta = False
        for fromfilename in lijst:  #fetch messages from ftp-server.
            try:
                ta_from = botslib.NewTransaction(filename='ftp:/'+posixpath.join(self.dirpath,fromfilename),
                                                    status=EXTERNIN,
                                                    fromchannel=self.channeldict['idchannel'],
                                                    idroute=self.idroute)
                ta_to =   ta_from.copyta(status=FILEIN)
                remove_ta = True
                tofilename = unicode(ta_to.idta)
                tofile = botslib.opendata(tofilename, 'wb')
                try:
                    if self.channeldict['ftpbinary']:
                        self.session.retrbinary("RETR " + fromfilename, tofile.write)
                    else:
                        self.session.retrlines("RETR " + fromfilename, lambda s, w=tofile.write: w(s+"\n"))
                except ftplib.error_perm as msg:
                    if unicode(msg)[:3] in [u'550',]:     #we are trying to download a directory...
                        raise botslib.BotsError(u'To be catched')
                    else:
                        raise
                tofile.close()
                filesize = os.path.getsize(botslib.abspathdata(tofilename))
                if not filesize:
                    raise botslib.BotsError(u'To be catched; directory (or empty file)')
            except botslib.BotsError:   #directory or empty file; handle exception but generate no error.
                if remove_ta:
                    try:
                        ta_from.delete()
                        ta_to.delete()
                    except:
                        pass
            except:
                txt = botslib.txtexc()
                botslib.ErrorProcess(functionname='ftp-incommunicate',errortext=txt,channeldict=self.channeldict)
                if remove_ta:
                    try:
                        ta_from.delete()
                        ta_to.delete()
                    except:
                        pass
            else:
                ta_to.update(filename=tofilename,statust=OK,filesize=filesize)
                ta_from.update(statust=DONE)
                if self.channeldict['remove']:
                    self.session.delete(fromfilename)
            finally:
                remove_ta = False
                if (datetime.datetime.now()-startdatetime).seconds >= self.maxsecondsperchannel:
                    break

 
    def outcommunicate(self):
        ''' do ftp: send files. To be used via receive-dispatcher.
            each to be send file is transaction.
            each send file is transaction.
            NB: ftp command APPE should be supported by server
        '''
        #get right filename_mask & determine if fixed name (append) or files with unique names
        filename_mask = self.channeldict['filename'] if self.channeldict['filename'] else '*'
        if '{overwrite}' in filename_mask:
            filename_mask = filename_mask.replace('{overwrite}','')
            mode = 'STOR '
        else:
            mode = 'APPE '
        for row in botslib.query('''SELECT idta,filename,numberofresends
                                    FROM ta
                                    WHERE idta>%(rootidta)s
                                      AND status=%(status)s
                                      AND statust=%(statust)s
                                      AND tochannel=%(tochannel)s
                                        ''',
                                    {'tochannel':self.channeldict['idchannel'],'rootidta':self.rootidta,
                                    'status':FILEOUT,'statust':OK}):
            try:
                ta_from = botslib.OldTransaction(row['idta'])
                ta_to = ta_from.copyta(status=EXTERNOUT)
                tofilename = self.filename_formatter(filename_mask,ta_from)
                if self.channeldict['ftpbinary']:
                    fromfile = botslib.opendata(row['filename'], 'rb')
                    self.session.storbinary(mode + tofilename, fromfile)
                else:
                    fromfile = botslib.opendata(row['filename'], 'r')
                    self.session.storlines(mode + tofilename, fromfile)
                fromfile.close()
                #Rename filename after writing file.
                #Function: safe file writing: do not want another process to read the file while it is being written.
                if self.channeldict['mdnchannel']:
                    tofilename_old = tofilename
                    tofilename = botslib.rreplace(tofilename_old,self.channeldict['mdnchannel'])
                    self.session.rename(tofilename_old,tofilename)
            except:
                txt = botslib.txtexc()
                ta_to.update(statust=ERROR,errortext=txt,filename='ftp:/'+posixpath.join(self.dirpath,tofilename),numberofresends=row['numberofresends']+1)
            else:
                ta_to.update(statust=DONE,filename='ftp:/'+posixpath.join(self.dirpath,tofilename),numberofresends=row['numberofresends']+1)
            finally:
                ta_from.update(statust=DONE)

    def disconnect(self):
        try:
            self.session.quit()
        except:
            self.session.close()
        


class sftp(_comsession):
    ''' SFTP: SSH File Transfer Protocol (SFTP is not FTP run over SSH, SFTP is not Simple File Transfer Protocol)
    '''
    def connect(self):
        # check dependencies
        try:
            import paramiko
        except:
            raise ImportError(_(u'Dependency failure: communicationtype "sftp" requires python library "paramiko".'))
        try:
            from Crypto import Cipher
        except:
            raise ImportError(_(u'Dependency failure: communicationtype "sftp" requires python library "pycrypto".'))

        if self.debug:
            # Convert ftpdebug to paramiko logging level (1=20=info, 2=10=debug)
            paramiko.util.log_to_file('/tmp/sftp.log', 30)
        hostkey = None
        pkey = None
        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        self.transport = paramiko.Transport((self.host, self.port or 22))
        self.transport.connect(username=self.username, password=self.password, hostkey=hostkey, pkey=pkey)
        self.session = paramiko.SFTPClient.from_transport(self.transport)
        #channel = self.session.get_channel()
        #channel.settimeout(10)
        self.set_cwd('.')

    def set_cwd(self, path):
        self.session.chdir('.') # getcwd does not work without this chdir first!
        wd = self.session.getcwd()
        if path:
            wd = posixpath.normpath(posixpath.join(wd,path))
            try:
                self.session.chdir(wd)
            except:
                self.session.mkdir(wd)
                self.session.chdir(wd)
        return wd

    def disconnect(self):
        self.session.close()
        self.transport.close()

    def list_files(self, path='.', pattern='*'):
        return fnmatch.filter(self.session.listdir(path), pattern)

    def get_file(self, filename):
        f = self.session.open(filename, 'r')    # SSH treats all files as binary
        content = f.read()
        f.close()
        return content
    
    def put_file(self, file_obj, name, force = False):
        if force or name not in self.list_files():
            self.session.putfo(file_obj, name, confirm=False) #Delivered messages do not show up on Strålfors' server, so confirm will generate an error even on success. 
            return True
        return False
    
    def rm(self, filename):
        self.session.remove(filename)

class edi_route(models.Model):
    _inherit = 'edi.route' 

    ftp_host = fields.Char(string="Host")
    ftp_user = fields.Char(string="User")
    ftp_password = fields.Char(string="Password")
    ftp_directory_in = fields.Char(string="Directory In",)
    ftp_directory_out = fields.Char(string="Directory Out",)
    ftp_pattern = fields.Char(string="Pattern", help="File pattern eg *.edi")
    ftp_debug = fields.Boolean(string="Debug")
    protocol = fields.Selection(selection_add=[('ftp', 'Ftp'), ('sftp', 'Sftp')])

    @api.one
    def check_connection(self):
        _logger.info('Check connection [%s:%s]' % (self.name, self.protocol))
        if self.protocol == 'ftp':
            pass
        elif self.protocol == 'sftp':
            server =  sftp(host=self.ftp_host, username=self.ftp_user, password=self.ftp_password, debug=self.ftp_debug)
            server.connect()
            server.disconnect()
        else:
            super(edi_route, self).check_connection()

    @api.multi
    def _run_in(self):
        if self.protocol == 'ftp':
            return []
        elif self.protocol == 'sftp':
            envelopes = []
            if self.ftp_debug:
                _logger.debug('sftp host=%s  username=%s password=%s' % (self.ftp_host, self.ftp_user, self.ftp_password))
            try:
                server =  sftp(host=self.ftp_host, username=self.ftp_user, password=self.ftp_password, debug=self.ftp_debug)
                server.connect()
            except Exception as e:
                self.log('error in sftp', sys.exc_info())
                _logger.error('error in sftp')
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
                    self.log('error in sftp', sys.exc_info())
                    _logger.error('error in sftp READ')
                finally:
                    server.disconnect()
            log = 'sftp host=%s  username=%s password=%s\nNbr envelopes %s\n%s' % (self.ftp_host, self.ftp_user, self.ftp_password, len(envelopes), ','.join([e.name for e in envelopes]))
            _logger.info(log)
            if self.ftp_debug:
                self.log(log)
            return envelopes
        else:
            super(edi_route, self)._run_in()

    @api.multi
    def _run_out(self, envelopes):
        _logger.debug('edi_route._run_out (sftp): %s' % envelopes)
        if self.protocol == 'ftp':
            pass
        elif self.protocol == 'sftp':
            if self.ftp_debug:
                _logger.debug('sftp host=%s  username=%s password=%s' % (self.ftp_host, self.ftp_user, self.ftp_password))
            try:
                server =  sftp(host=self.ftp_host, username=self.ftp_user, password=self.ftp_password, debug=self.ftp_debug)
                server.connect()
            except Exception as e:
                if self.ftp_debug:
                    self.log('error in sftp', sys.exc_info())
                _logger.error('error in sftp')
            else:
                try:
                    server.set_cwd(self.ftp_directory_out or '.')
                    f_list = server.list_files(pattern=self.ftp_pattern or '*')
                    if self.ftp_debug:
                        _logger.info('info list %s' % f_list)
                    for envelope in envelopes:
                        try:
                            file_obj = StringIO(base64.b64decode(envelope.body))
                            if server.put_file(file_obj, envelope.name):
                                envelope.state = 'sent'
                                for msg in envelope.edi_message_ids:
                                    msg.state = 'sent'
                            else:
                                envelope.state = 'canceled'
                                for msg in envelope.edi_message_ids:
                                    msg.state = 'canceled'
                                self.log('Error! Envelope %s already exists on server.' % envelope.name, sys.exc_info())
                        except Exception as e:
                            self.log('error when sending envelope %s' % envelope.name, sys.exc_info())    
                            envelope.state = 'canceled'
                            for msg in envelope.edi_message_ids:
                                msg.state = 'canceled'
                except Exception as e:
                    self.log('error in sftp with envelope %s' % envelope.name, sys.exc_info())
                    _logger.error('error in sftp READ')
                finally:
                    server.disconnect()
            log = 'sftp host=%s  username=%s password=%s\nNbr envelopes %s\n%s' % (self.ftp_host, self.ftp_user, self.ftp_password, len(envelopes), ','.join([e.name for e in envelopes]))
            _logger.info(log)
            if self.ftp_debug:
                self.log(log)
        else:
            super(edi_route, self)._run_out(envelopes)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
