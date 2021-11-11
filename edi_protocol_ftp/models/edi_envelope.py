# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
if sys.version_info[0] > 2:
    basestring = unicode = str
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
from bots import botslib
from ftplib import FTP_TLS, FTP

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
        self.ftpaccount = None
        self.ftpactive = False
        self.channeldict = {}
        self.dirpath = None
        self.idroute = None
        self.maxsecondsperchannel = None
        self.rootidta = None

    def connect(self):
        pass

    def disconnect(self):
        pass

    def set_cwd(self, path):
        self.session.chdir('.')  # getcwd does not work without this chdir first!
        wd = self.session.getcwd()
        if path:
            wd = posixpath.normpath(posixpath.join(wd, path))
            try:
                self.session.chdir(wd)
            except:
                self.session.mkdir(wd)
                self.session.chdir(wd)
        return wd

    def convertcodecformime(codec_in):
        convertdict = {
            'ascii': 'us-ascii',
            'unoa': 'us-ascii',
            'unob': 'us-ascii',
            'unoc': 'iso-8859-1',
        }
        codec_res = codec_in.lower().replace('_', '-')
        return convertdict.get(codec_res, codec_in)


class ftp(_comsession):
    def connect(self):
        self.session = ftplib.FTP()
        self.session.set_debuglevel(2 if self.debug else 0)  # set debug level (0=no, 1=medium, 2=full debug)
        self.session.set_pasv(not self.ftpactive)  # active or passive ftp
        self.session.connect(host=self.host, port=self.port or 21)
        self.session.login(user=self.username, passwd=self.password, acct=self.ftpaccount)
        self.set_cwd(path='')

    def set_cwd(self, path):
        self.session.cwd('.')  # getcwd does not work without this chdir first!
        wd = self.session.pwd()
        if path:
            wd = posixpath.normpath(posixpath.join(wd, path))
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
        try:  # some ftp servers give errors when directory is empty; catch these errors here
            files = self.session.nlst()
        except (ftplib.error_perm, ftplib.error_temp) as msg:
            if unicode(msg)[:3] not in [u'550', u'450']:
                raise

        lijst = fnmatch.filter(files, self.channeldict['filename'])
        remove_ta = False
        for fromfilename in lijst:  # fetch messages from ftp-server.
            try:
                ta_from = botslib.NewTransaction(filename='ftp:/' + posixpath.join(self.dirpath, fromfilename),
                                                 status='EXTERNIN',
                                                 fromchannel=self.channeldict['idchannel'],
                                                 idroute=self.idroute)
                ta_to = ta_from.copyta(status='FILEIN')
                remove_ta = True
                tofilename = unicode(ta_to.idta)
                tofile = botslib.opendata(tofilename, 'wb')
                try:
                    if self.channeldict['ftpbinary']:
                        self.session.retrbinary("RETR " + fromfilename, tofile.write)
                    else:
                        self.session.retrlines("RETR " + fromfilename, lambda s, w=tofile.write: w(s + "\n"))
                except ftplib.error_perm as msg:
                    if unicode(msg)[:3] in [u'550', ]:  # we are trying to download a directory...
                        raise botslib.BotsError(u'To be catched')
                    else:
                        raise
                tofile.close()
                filesize = os.path.getsize(botslib.abspathdata(tofilename))
                if not filesize:
                    raise botslib.BotsError(u'To be catched; directory (or empty file)')
            except botslib.BotsError:  # directory or empty file; handle exception but generate no error.
                if remove_ta:
                    try:
                        ta_from.delete()
                        ta_to.delete()
                    except:
                        pass
            except:
                txt = botslib.txtexc()
                botslib.ErrorProcess(functionname='ftp-incommunicate', errortext=txt, channeldict=self.channeldict)
                if remove_ta:
                    try:
                        ta_from.delete()
                        ta_to.delete()
                    except:
                        pass
            else:
                ta_to.update(filename=tofilename, status='OK', filesize=filesize)
                ta_from.update(status='DONE')
                if self.channeldict['remove']:
                    self.session.delete(fromfilename)
            finally:
                remove_ta = False
                if (datetime.datetime.now() - startdatetime).seconds >= self.maxsecondsperchannel:
                    break

    def outcommunicate(self):
        ''' do ftp: send files. To be used via receive-dispatcher.
            each to be send file is transaction.
            each send file is transaction.
            NB: ftp command APPE should be supported by server
        '''
        # get right filename_mask & determine if fixed name (append) or files with unique names
        filename_mask = self.channeldict['filename'] if self.channeldict['filename'] else '*'
        if '{overwrite}' in filename_mask:
            filename_mask = filename_mask.replace('{overwrite}', '')
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
                                 {'tochannel': self.channeldict['idchannel'], 'rootidta': self.rootidta, 'status': 'OK'}):
            try:
                ta_from = botslib.OldTransaction(row['idta'])
                ta_to = ta_from.copyta(status='EXTERNOUT')
                tofilename = self.filename_formatter(filename_mask, ta_from)
                if self.channeldict['ftpbinary']:
                    fromfile = botslib.opendata(row['filename'], 'rb')
                    self.session.storbinary(mode + tofilename, fromfile)
                else:
                    fromfile = botslib.opendata(row['filename'], 'r')
                    self.session.storlines(mode + tofilename, fromfile)
                fromfile.close()
                # Rename filename after writing file.
                # Function: safe file writing: do not want another process to read the file while it is being written.
                if self.channeldict['mdnchannel']:
                    tofilename_old = tofilename
                    tofilename = botslib.rreplace(tofilename_old, self.channeldict['mdnchannel'])
                    self.session.rename(tofilename_old, tofilename)
            except:
                txt = botslib.txtexc()
                ta_to.update(status='ERROR', errortext=txt, filename='ftp:/' + posixpath.join(self.dirpath, tofilename),
                             numberofresends=row['numberofresends'] + 1)
            else:
                ta_to.update(status='DONE', filename='ftp:/' + posixpath.join(self.dirpath, tofilename),
                             numberofresends=row['numberofresends'] + 1)
            finally:
                ta_from.update(status='DONE')

    def filename_formatter(self, mask, xfrom):
        pass

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
        # channel = self.session.get_channel()
        # channel.settimeout(10)
        self.set_cwd('.')

    def set_cwd(self, path):
        self.session.chdir('.')  # getcwd does not work without this chdir first!
        wd = self.session.getcwd()
        if path:
            wd = posixpath.normpath(posixpath.join(wd, path))
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
        f = self.session.open(filename, 'r')  # SSH treats all files as binary
        content = f.read()
        f.close()
        return content

    def put_file(self, file_obj, name, force=False):
        if force or name not in self.list_files():
            self.session.putfo(file_obj, name,
                               confirm=False)  # Delivered messages do not show up on Strålfors' server, so confirm will generate an error even on success.
            return True
        return False

    def rm(self, filename):
        self.session.remove(filename)


class EdiEnvelopeRest(models.Model):
    _inherit = "edi.envelope"

    def send(self):
        """Send the envelope via FTP"""
        if self.protocol_id.id == self.env.ref('edi_protocol_ftp.ftp_edi_protocol_type').id:
            ftp = FTP()
            ftp.connect(self.host, self.port)
            ftp.login(self.username, self.password)
            ftp.cwd('/report')

        return super(EdiEnvelopeRest, self).send()

    @api.model
    def receive(self):
        if self.protocol_id.id == self.env.ref('edi_protocol_ftp.ftp_edi_protocol_type').id:
            pass
        return super(EdiEnvelopeRest, self).receive()
