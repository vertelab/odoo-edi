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

import logging
_logger = logging.getLogger(__name__)


class _comsession(object):
    ''' Abstract class for communication-session. Use only subclasses.
        Subclasses are called by dispatcher function 'run'
    '''
    def __init__(self,host='localhost',username=None,password=None,port=None,debug=False):
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
        standard port to connect to is port 22.
        requires paramiko and pycrypto to be installed
        based on class ftp and ftps above with code from demo_sftp.py which is included with paramiko
        Mike Griffin 16/10/2010
        Henk-jan ebbers 20110802: when testing I found that the transport also needs to be closed. So changed transport ->self.transport, and close this in disconnect
        henk-jan ebbers 20111019: disabled the host_key part for now (but is very interesting). Is not tested; keys should be integrated in bots also for other protocols.
        henk-jan ebbers 20120522: hostkey and privatekey can now be handled in user exit.
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
            log_file = 'sftp.log'
            # Convert ftpdebug to paramiko logging level (1=20=info, 2=10=debug)
            paramiko.util.log_to_file('/tmp/sftp.log', 30)

      
        #~ if self.userscript and hasattr(self.userscript,'hostkey'):
            #~ hostkey = botslib.runscript(self.userscript,self.scriptname,'hostkey',channeldict=self.channeldict)
        #~ else:
            #~ hostkey = None
        #~ if self.userscript and hasattr(self.userscript,'privatekey'):
            #~ privatekeyfile,pkeytype,pkeypassword = botslib.runscript(self.userscript,self.scriptname,'privatekey',channeldict=self.channeldict)
            #~ if pkeytype == 'RSA':
                #~ pkey = paramiko.RSAKey.from_private_key_file(filename=privatekeyfile,password=pkeypassword)
            #~ else:
                #~ pkey = paramiko.DSSKey.from_private_key_file(filename=privatekeyfile,password=pkeypassword)
        #~ else:
            #~ pkey = None
        hostkey = None
        pkey = None

        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        self.transport = paramiko.Transport((self.host,self.port or 22))
        self.transport.connect(username=self.username,password=self.password,hostkey=hostkey,pkey=pkey)
        self.session = paramiko.SFTPClient.from_transport(self.transport)
        #channel = self.session.get_channel()
        #channel.settimeout(10)
        self.set_cwd('.')
        self

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
        
    def disconnect(self):
        self.session.close()
        self.transport.close()

  
    def list_files(self,path='.',pattern='*'):
        ''' do ftp: receive files. To be used via receive-dispatcher.
            each to be imported file is transaction.
            each imported file is transaction.
        '''
        if path != '.':
            self.set_cwd(path)
        return fnmatch.filter(self.session.listdir('.'),pattern)
        
    def get_file(self,filename):
        f = self.session.open(filename, 'r')    # SSH treats all files as binary
        content = f.read()
        f.close()
        return content

            
class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    ftp_host = fields.Char(string="Host",required=True)
    ftp_user = fields.Char(string="User",required=True)
    ftp_password = fields.Char(string="Password",required=True)
    ftp_directory = fields.Char(string="Directory",)
    ftp_pattern = fields.Char(string="Pattern",help="File pattern eg *.edi")
    ftp_debug = fields.Boolean(string="Debug")

    def _route_type(self):
        return [t for t in super(edi_route, self)._route_type() + [('ftp','Ftp'),('sftp','Sftp')] if not t[0] == 'none']
    @api.one
    def check_connection(self):
        _logger.info('Check connection [%s:%s]' % (self.name,self.route_type))
        if self.route_type == 'ftp':
            pass
        elif self.route_type == 'sftp':
            pass
        else:
            super(edi_route, self).check_connection()
    
    @api.one
    def run(self):
        super(edi_route, self).run()
        _logger.info('run [%s:%s]' % (self.name,self.route_type))
        envelops = []
        if self.route_type == 'ftp':
            pass
        elif self.route_type == 'sftp':
            if self.ftp_debug:
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
