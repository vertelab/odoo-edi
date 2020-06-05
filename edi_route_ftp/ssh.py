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
            paramiko.util.log_to_file('sftp.log', 30)

      
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
        
    def incommunicate(self):
        ''' do ftp: receive files. To be used via receive-dispatcher.
            each to be imported file is transaction.
            each imported file is transaction.
        '''
        startdatetime = datetime.datetime.now()
        files = self.session.listdir('.')
        lijst = fnmatch.filter(files,self.channeldict['filename'])
        remove_ta = False
        for fromfilename in lijst:  #fetch messages from sftp-server.
            try:
                ta_from = botslib.NewTransaction(filename='sftp:/'+posixpath.join(self.dirpath,fromfilename),
                                                    status=EXTERNIN,
                                                    fromchannel=self.channeldict['idchannel'],
                                                    idroute=self.idroute)
                ta_to =   ta_from.copyta(status=FILEIN)
                remove_ta = True
                tofilename = unicode(ta_to.idta)
                fromfile = self.session.open(fromfilename, 'r')    # SSH treats all files as binary
                content = fromfile.read()
                filesize = len(content)
                tofile = botslib.opendata(tofilename, 'wb')
                tofile.write(content)
                tofile.close()
                fromfile.close()
            except:
                txt = botslib.txtexc()
                botslib.ErrorProcess(functionname='sftp-incommunicate',errortext=txt,channeldict=self.channeldict)
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
                    self.session.remove(fromfilename)
            finally:
                remove_ta = False
                if (datetime.datetime.now()-startdatetime).seconds >= self.maxsecondsperchannel:
                    break

  
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
        
server =  sftp(host='localhost',username='aw',password='cQfy7dJE',debug=True)


server.connect()
print (server.session)
print (server.session.getcwd())
for f in server.list_files(path='Dokument',pattern='*.txt'):
    print (server.get_file(f))
server.disconnect()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
