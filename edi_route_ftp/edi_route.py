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

import logging
_logger = logging.getLogger(__name__)

class _comsession(object):
    ''' Abstract class for communication-session. Use only subclasses.
        Subclasses are called by dispatcher function 'run'
    '''
    def __init__(self,channeldict,idroute,userscript,scriptname,command,rootidta):
        self.channeldict = channeldict
        self.idroute = idroute
        self.userscript = userscript
        self.scriptname = scriptname
        self.command = command
        self.rootidta = rootidta

    def run(self):
        if self.channeldict['inorout'] == 'out':
            self.precommunicate()
            self.connect()
            self.outcommunicate()
            self.disconnect()
            self.archive()
        else:   #incommunication
            if self.command == 'new': #only in-communicate for new run
                #handle maxsecondsperchannel: use global value from bots.ini unless specified in channel. (In database this is field 'rsrv2'.)
                self.maxsecondsperchannel = botsglobal.ini.getint('settings','maxsecondsperchannel',sys.maxint) if self.channeldict['rsrv2'] <= 0 else self.channeldict['rsrv2']
                try:
                    self.connect()
                except:     #in-connection failed. note that no files are received yet. useful if scheduled quite often, and you do nto want error-report eg when server is down. 
                    #max_nr_retry : get this from channel. should be integer, but only textfields where left. so might be ''/None->use 0
                    max_nr_retry = int(self.channeldict['rsrv1']) if self.channeldict['rsrv1'] else 0
                    if max_nr_retry:
                        domain = u'bots_communication_failure_' + self.channeldict['idchannel']
                        nr_retry = botslib.unique(domain)  #update nr_retry in database
                        if nr_retry >= max_nr_retry:
                            botslib.unique(domain,updatewith=0)    #reset nr_retry to zero
                            #raises exception
                        else:
                            return  #just return if max_nr_retry is not reached
                    raise
                else:   #in-connection OK
                    #max_nr_retry : get this from channel. should be integer, but only textfields where left. so might be ''/None->use 0
                    max_nr_retry = int(self.channeldict['rsrv1']) if self.channeldict['rsrv1'] else 0
                    if max_nr_retry:
                        domain = u'bots_communication_failure_' + self.channeldict['idchannel']
                        botslib.unique(domain,updatewith=0)    #set nr_retry to zero 
                self.incommunicate()
                self.disconnect()
            self.postcommunicate()
            self.archive()


    def archive(self):
        ''' after the communication channel has ran, archive received of send files.
            archivepath is the root directory for the archive (for this channel).
            within the archivepath files are stored by default as [archivepath]/[date]/[unique_filename]
            
        '''
        if not self.channeldict['archivepath']:
            return  #do not archive if not indicated
        if botsglobal.ini.getboolean('acceptance','runacceptancetest',False): 
            return  #do not archive in acceptance testing
        if self.channeldict['filename'] and self.channeldict['type'] in ('file','ftp','ftps','ftpis','sftp','mimefile','communicationscript'):
            archiveexternalname = botsglobal.ini.getboolean('settings','archiveexternalname',False) #use external filename in archive 
        else:
            archiveexternalname = False
        if self.channeldict['inorout'] == 'in':
            status = FILEIN
            statust = OK
            channel = 'fromchannel'
        else:
            if archiveexternalname:
                status = EXTERNOUT
            else:
                status = FILEOUT
            statust = DONE
            channel = 'tochannel'
        #user script can manipulate archivepath
        if self.userscript and hasattr(self.userscript,'archivepath'):
            archivepath = botslib.runscript(self.userscript,self.scriptname,'archivepath',channeldict=self.channeldict)
        else:
            archivepath = botslib.join(self.channeldict['archivepath'],time.strftime('%Y%m%d'))
        archivezip = botsglobal.ini.getboolean('settings','archivezip',False)   #archive to zip or not
        if archivezip:
            archivepath += '.zip'
        checkedifarchivepathisthere = False  #for a outchannel that is less used, lots of empty dirs will be created. This var is used to check within loop if dir exist, but this is only checked one time.
        for row in botslib.query('''SELECT filename,idta
                                    FROM  ta
                                    WHERE idta>%(rootidta)s
                                    AND   status=%(status)s
                                    AND   statust=%(statust)s
                                    AND   ''' + channel + '''=%(idchannel)s
                                    ''',
                                    {'idchannel':self.channeldict['idchannel'],'status':status,
                                    'statust':statust,'rootidta':self.rootidta}):
            if not checkedifarchivepathisthere:
                if archivezip:
                    botslib.dirshouldbethere(os.path.dirname(archivepath))
                    archivezipfilehandler = zipfile.ZipFile(archivepath,'a',zipfile.ZIP_DEFLATED)
                else:
                    botslib.dirshouldbethere(archivepath)
                checkedifarchivepathisthere = True

            if archiveexternalname:
                if self.channeldict['inorout'] == 'in':
                    # we have internal filename, get external
                    absfilename = botslib.abspathdata(row['filename'])
                    taparent = botslib.OldTransaction(idta=row['idta'])
                    ta_list = botslib.trace_origin(ta=taparent,where={'status':EXTERNIN})
                    if ta_list:
                        archivename = os.path.basename(ta_list[-1].filename)
                    else:
                        archivename = row['filename']
                else:
                    # we have external filename, get internal
                    archivename = os.path.basename(row['filename'])
                    taparent = botslib.OldTransaction(idta=row['idta'])
                    ta_list = botslib.trace_origin(ta=taparent,where={'status':FILEOUT})
                    absfilename = botslib.abspathdata(ta_list[0].filename)
            else:
                # use internal name in archive
                absfilename = botslib.abspathdata(row['filename'])
                archivename = os.path.basename(row['filename'])

            if self.userscript and hasattr(self.userscript,'archivename'):
                archivename = botslib.runscript(self.userscript,self.scriptname,'archivename',channeldict=self.channeldict,idta=row['idta'],filename=absfilename)
            #~print 'archive',os.path.basename(absfilename),'as',archivename

            if archivezip:
                archivezipfilehandler.write(absfilename,archivename)
            else:
                # if a file of the same name already exists, add a timestamp
                if os.path.isfile(botslib.join(archivepath,archivename)):
                    archivename = os.path.splitext(archivename)[0] + time.strftime('_%H%M%S') + os.path.splitext(archivename)[1]
                shutil.copy(absfilename,botslib.join(archivepath,archivename))

        if archivezip and checkedifarchivepathisthere:
            archivezipfilehandler.close()


    def postcommunicate(self):
        pass

    def precommunicate(self):
        pass

    def file2mime(self):
        ''' convert 'plain' files into email (mime-document).
            1 edi file always in 1 mail.
            from status FILEOUT to FILEOUT
        '''
        #select files with right statust, status and channel.
        for row in botslib.query('''SELECT idta,filename,frompartner,topartner,charset,contenttype,editype
                                    FROM ta
                                    WHERE idta>%(rootidta)s
                                    AND status=%(status)s
                                    AND statust=%(statust)s
                                    AND tochannel=%(idchannel)s
                                    ''',
                                    {'idchannel':self.channeldict['idchannel'],'status':FILEOUT,
                                    'statust':OK,'idroute':self.idroute,'rootidta':self.rootidta}):
            try:
                ta_from = botslib.OldTransaction(row['idta'])
                ta_to = ta_from.copyta(status=FILEOUT)
                ta_to.synall()  #needed for user exits: get all parameters of ta_to from database;
                confirmtype = u''
                confirmasked = False
                charset = row['charset']

                if row['editype'] == 'email-confirmation': #outgoing MDN: message is already assembled
                    outfilename = row['filename']
                else:   #assemble message: headers and payload. Bots uses simple MIME-envelope; by default payload is an attachment
                    message = email.Message.Message()
                    #set 'from' header (sender)
                    frommail,ccfrom_not_used_variable = self.idpartner2mailaddress(row['frompartner'])    #lookup email address for partnerID
                    message.add_header('From', frommail)

                    #set 'to' header (receiver)
                    if self.userscript and hasattr(self.userscript,'getmailaddressforreceiver'):    #user exit to determine to-address/receiver
                        tomail,ccto = botslib.runscript(self.userscript,self.scriptname,'getmailaddressforreceiver',channeldict=self.channeldict,ta=ta_to)
                    else:
                        tomail,ccto = self.idpartner2mailaddress(row['topartner'])          #lookup email address for partnerID
                    message.add_header('To',tomail)
                    if ccto:
                        message.add_header('CC',ccto)

                    if botsglobal.ini.getboolean('acceptance','runacceptancetest',False):
                        reference = '123message-ID email should be unique123'
                        email_datetime = email.Utils.formatdate(timeval=time.mktime(time.strptime("2013-01-23 01:23:45", "%Y-%m-%d %H:%M:%S")),localtime=True)
                    else:
                        reference = email.Utils.make_msgid(unicode(ta_to.idta))    #use transaction idta in message id.
                        email_datetime = email.Utils.formatdate(localtime=True)
                    message.add_header('Message-ID',reference)
                    message.add_header("Date",email_datetime)
                    ta_to.update(frommail=frommail,tomail=tomail,cc=ccto,reference=reference)   #update now (in order to use correct & updated ta_to in userscript)

                    #set Disposition-Notification-To: ask/ask not a a MDN?
                    if botslib.checkconfirmrules('ask-email-MDN',idroute=self.idroute,idchannel=self.channeldict['idchannel'],
                                                                frompartner=row['frompartner'],topartner=row['topartner']):
                        message.add_header("Disposition-Notification-To",frommail)
                        confirmtype = u'ask-email-MDN'
                        confirmasked = True

                    #set subject
                    if botsglobal.ini.getboolean('acceptance','runacceptancetest',False):
                        subject = u'12345678'
                    else:
                        subject = unicode(row['idta'])
                    content = botslib.readdata(row['filename'])     #get attachment from data file
                    if self.userscript and hasattr(self.userscript,'subject'):    #user exit to determine subject
                        subject = botslib.runscript(self.userscript,self.scriptname,'subject',channeldict=self.channeldict,ta=ta_to,subjectstring=subject,content=content)
                    message.add_header('Subject',subject)

                    #set MIME-version
                    message.add_header('MIME-Version','1.0')

                    #set attachment filename
                    filename_mask = self.channeldict['filename'] if self.channeldict['filename'] else '*'
                    attachmentfilename = self.filename_formatter(filename_mask,ta_to)
                    if attachmentfilename and self.channeldict['sendmdn'] != 'body':  #if not explicitly indicated 'as body' or (old)  if attachmentfilename is None or empty string: do not send as an attachment.
                        message.add_header("Content-Disposition",'attachment',filename=attachmentfilename)

                    #set Content-Type and charset
                    charset = self.convertcodecformime(row['charset'])
                    message.add_header('Content-Type',row['contenttype'].lower(),charset=charset)          #contenttype is set in grammar.syntax

                    #set attachment/payload; the Content-Transfer-Encoding is set by python encoder
                    message.set_payload(content)   #do not use charset; this lead to unwanted encodings...bots always uses base64
                    if self.channeldict['askmdn'] == 'never':       #channeldict['askmdn'] is the Mime encoding
                        email.encoders.encode_7or8bit(message)      #no encoding; but the Content-Transfer-Encoding is set to 7-bit or 8-bt
                    elif self.channeldict['askmdn'] == 'ascii' and charset == 'us-ascii':
                        pass        #do nothing: ascii is default encoding
                    else:           #if Mime encoding is 'always' or  (Mime encoding == 'ascii' and charset!='us-ascii'): use base64
                        email.encoders.encode_base64(message)

                    #*******write email to file***************************
                    outfilename = unicode(ta_to.idta)
                    outfile = botslib.opendata(outfilename, 'wb')
                    generator = email.Generator.Generator(outfile, mangle_from_=False, maxheaderlen=78)
                    generator.flatten(message,unixfrom=False)
                    outfile.close()
            except:
                txt = botslib.txtexc()
                ta_to.update(statust=ERROR,errortext=txt)
            else:
                ta_to.update(statust=OK,filename=outfilename,confirmtype=confirmtype,confirmasked=confirmasked,charset=charset)
            finally:
                ta_from.update(statust=DONE)
        return

    def mime2file(self):
        ''' convert emails (mime-documents) to 'plain' files.
            from status FILEIN to FILEIN
            process emails:
            -   extract information (eg sender-address)
            -   generate MDN (if asked and OK from bots-configuration)
            -   process MDN
            -   save 'attachments' as files
            -   filter emails/attachments based on contenttype
            -   email-address should be know by bots (can be turned off)
        '''
        whitelist_multipart = ['multipart/mixed','multipart/digest','multipart/signed','multipart/report','message/rfc822','multipart/alternative']
        whitelist_major = ['text','application']
        blacklist_contenttype = ['text/html','text/enriched','text/rtf','text/richtext','application/postscript','text/vcard','text/css']
        def savemime(msg):
            ''' save contents of email as separate files.
                is a nested function.
                3x filtering:
                -   whitelist of multipart-contenttype
                -   whitelist of body-contentmajor
                -   blacklist of body-contentytpe
            '''
            nrmimesaved = 0     #count nr of valid 'attachments'
            contenttype     = msg.get_content_type()
            if msg.is_multipart():
                if contenttype in whitelist_multipart:
                    for part in msg.get_payload():
                        nrmimesaved += savemime(part)
            else:    #is not a multipart
                if msg.get_content_maintype() not in whitelist_major or contenttype in blacklist_contenttype:
                    return 0
                content = msg.get_payload(decode=True)
                if not content or content.isspace():
                    return 0
                charset = msg.get_content_charset('ascii')
                if self.userscript and hasattr(self.userscript,'accept_incoming_attachment'):
                    accept_attachment = botslib.runscript(self.userscript,self.scriptname,'accept_incoming_attachment',channeldict=self.channeldict,ta=ta_from,charset=charset,content=content,contenttype=contenttype)
                    if not accept_attachment:
                        return 0
                filesize = len(content)
                ta_file = ta_from.copyta(status=FILEIN)
                outfilename = unicode(ta_file.idta)
                outfile = botslib.opendata(outfilename, 'wb')
                outfile.write(content)
                outfile.close()
                nrmimesaved += 1
                ta_file.update(statust=OK,
                                contenttype=contenttype,
                                charset=charset,
                                filename=outfilename,
                                filesize=filesize)
            return nrmimesaved
        #*****************end of nested function savemime***************************
        @botslib.log_session
        def mdnreceive():
            tmp = msg.get_param('reporttype')
            if tmp is None or email.Utils.collapse_rfc2231_value(tmp)!='disposition-notification':    #invalid MDN
                raise botslib.CommunicationInError(_(u'Received email-MDN with errors.'))
            for part in msg.get_payload():
                if part.get_content_type()=='message/disposition-notification':
                    originalmessageid = part['original-message-id']
                    if originalmessageid is not None:
                        break
            else:   #invalid MDN: 'message/disposition-notification' not in email
                raise botslib.CommunicationInError(_(u'Received email-MDN with errors.'))
            botslib.changeq('''UPDATE ta
                               SET confirmed=%(confirmed)s, confirmidta=%(confirmidta)s
                               WHERE reference=%(reference)s
                               AND status=%(status)s
                               AND confirmasked=%(confirmasked)s
                               AND confirmtype=%(confirmtype)s
                               ''',
                                {'status':FILEOUT,'reference':originalmessageid,'confirmed':True,'confirmtype':'ask-email-MDN','confirmidta':ta_from.idta,'confirmasked':True})
            #for now no checking if processing was OK.....
            #performance: not good. Index should be on the reference.
        @botslib.log_session
        def mdnsend(ta_from):
            if not botslib.checkconfirmrules('send-email-MDN',idroute=self.idroute,idchannel=self.channeldict['idchannel'],
                                                            frompartner=frompartner,topartner=topartner):
                return 0 #do not send
            #make message
            message = email.Message.Message()
            message.add_header('From',tomail)
            dispositionnotificationto = email.Utils.parseaddr(msg['disposition-notification-to'])[1]
            message.add_header('To', dispositionnotificationto)
            message.add_header('Subject', 'Return Receipt (displayed) - '+subject)
            message.add_header('MIME-Version','1.0')
            message.add_header('Content-Type','multipart/report',reporttype='disposition-notification')
            #~ message.set_type('multipart/report')
            #~ message.set_param('reporttype','disposition-notification')

            #make human readable message
            humanmessage = email.Message.Message()
            humanmessage.add_header('Content-Type', 'text/plain')
            humanmessage.set_payload('This is an return receipt for the mail that you send to '+tomail)
            message.attach(humanmessage)

            #make machine readable message
            machinemessage = email.Message.Message()
            machinemessage.add_header('Content-Type', 'message/disposition-notification')
            machinemessage.add_header('Original-Message-ID', reference)
            nep = email.Message.Message()
            machinemessage.attach(nep)
            message.attach(machinemessage)

            #write email to file;
            ta_mdn = botslib.NewTransaction(status=MERGED)  #new transaction for group-file
            
            if botsglobal.ini.getboolean('acceptance','runacceptancetest',False):
                mdn_reference = '123message-ID email should be unique123'
                mdn_datetime = email.Utils.formatdate(timeval=time.mktime(time.strptime("2013-01-23 01:23:45", "%Y-%m-%d %H:%M:%S")),localtime=True)
            else:
                mdn_reference = email.Utils.make_msgid(unicode(ta_mdn.idta))    #we first have to get the mda-ta to make this reference
                mdn_datetime = email.Utils.formatdate(localtime=True)
            message.add_header('Date',mdn_datetime)
            message.add_header('Message-ID', mdn_reference)
            
            mdnfilename = unicode(ta_mdn.idta)
            mdnfile = botslib.opendata(mdnfilename, 'wb')
            generator = email.Generator.Generator(mdnfile, mangle_from_=False, maxheaderlen=78)
            generator.flatten(message,unixfrom=False)
            mdnfile.close()
            ta_mdn.update(statust=OK,
                            idroute=self.idroute,
                            filename=mdnfilename,
                            editype='email-confirmation',
                            frompartner=topartner,
                            topartner=frompartner,
                            frommail=tomail,
                            tomail=dispositionnotificationto,
                            reference=mdn_reference,
                            content='multipart/report',
                            fromchannel=self.channeldict['idchannel'],
                            charset='ascii',
                            parent=ta_from.idta)
            return ta_mdn.idta
        #*****************end of nested function dispositionnotification***************************
        #get received mails for channel
        for row in botslib.query('''SELECT idta,filename
                                    FROM ta
                                    WHERE idta>%(rootidta)s
                                    AND status=%(status)s
                                    AND statust=%(statust)s
                                    AND fromchannel=%(fromchannel)s
                                    ''',
                                    {'status':FILEIN,'statust':OK,'rootidta':self.rootidta,
                                    'fromchannel':self.channeldict['idchannel'],'idroute':self.idroute}):
            try:
                #default values for sending MDN; used to update ta if MDN is not asked
                confirmtype = ''
                confirmed = False
                confirmasked = False
                confirmidta = 0
                #read & parse email
                ta_from = botslib.OldTransaction(row['idta'])
                infile = botslib.opendata(row['filename'], 'rb')
                msg             = email.message_from_file(infile)   #read and parse mail
                infile.close()
                #******get information from email (sender, receiver etc)***********************************************************
                reference       = self.checkheaderforcharset(msg['message-id'])
                subject = self.checkheaderforcharset(msg['subject'])
                contenttype     = self.checkheaderforcharset(msg.get_content_type())
                #frompartner (incl autorization)
                frommail        = self.checkheaderforcharset(email.Utils.parseaddr(msg['from'])[1])
                frompartner = ''
                if not self.channeldict['starttls']:    #starttls in channeldict is: 'no check on "from:" email adress'
                    frompartner = self.mailaddress2idpartner(frommail)
                    if frompartner is None:
                        raise botslib.CommunicationInError(_(u'"From" emailaddress(es) %(email)s not authorised/unknown for channel "%(idchannel)s".'),
                                                            {'email':frommail,'idchannel':self.channeldict['idchannel']})
                #topartner, cc (incl autorization)
                list_to_address = [self.checkheaderforcharset(address) for name_not_used_variable,address in email.Utils.getaddresses(msg.get_all('to', []))] 
                list_cc_address = [self.checkheaderforcharset(address) for name_not_used_variable,address in email.Utils.getaddresses(msg.get_all('cc', []))] 
                cc_content      = ','.join([address for address in (list_to_address + list_cc_address)])
                topartner = ''  #initialise topartner
                tomail = ''     #initialise tomail
                if not self.channeldict['apop']:    #apop in channeldict is: 'no check on "to:" email adress'
                    for address in list_to_address:   #all tos-addresses are checked; only one needs to be authorised.
                        topartner =  self.mailaddress2idpartner(address)
                        tomail = address
                        if topartner is not None:   #if topartner found: break out of loop
                            break
                    else:   #if no valid topartner: generate error
                        raise botslib.CommunicationInError(_(u'"To" emailaddress(es) %(email)s not authorised/unknown for channel "%(idchannel)s".'),
                                                            {'email':list_to_address,'idchannel':self.channeldict['idchannel']})
 
                #update transaction of mail with information found in mail
                ta_from.update(frommail=frommail,   #why save now not later: when saving the attachments need the amil-header-info to be in ta (copyta)
                                tomail=tomail,
                                reference=reference,
                                contenttype=contenttype,
                                frompartner=frompartner,
                                topartner=topartner,
                                cc = cc_content,
                                rsrv1 = subject)
                if contenttype == 'multipart/report':   #process received MDN confirmation
                    mdnreceive()
                else:
                    if msg.has_key('disposition-notification-To'):  #sender requests a MDN
                        confirmidta = mdnsend(ta_from)
                        if confirmidta:
                            confirmtype = 'send-email-MDN'
                            confirmed = True
                            confirmasked = True
                    nrmimesaved = savemime(msg)
                    if not nrmimesaved:
                        raise botslib.CommunicationInError (_(u'No valid attachment in received email'))
            except:
                txt = botslib.txtexc()
                ta_from.update(statust=ERROR,errortext=txt)
                ta_from.deletechildren()
            else:
                ta_from.update(statust=DONE,confirmtype=confirmtype,confirmed=confirmed,confirmasked=confirmasked,confirmidta=confirmidta)
        return

    @staticmethod
    def checkheaderforcharset(org_header):
        ''' correct handling of charset for email headers that are saved in database.
        ''' 
        header,encoding = email.header.decode_header(org_header)[0]    #for subjects with non-ascii content special notation exists in MIME-standard
        try:
            if encoding is not None:
                return header.decode(encoding)                       #decode (to unicode)
            #test if valid; use case: spam... need to test because database-storage will give errors otherwise. 
            header.encode('utf8')
            return header
        except:
            raise botslib.CommunicationInError(_(u'Email header invalid - probably issues with characterset.'))
                        
    def mailaddress2idpartner(self,mailaddress):
        ''' lookup email address to see if know in configuration. '''
        mailaddress_lower = mailaddress.lower()
        #first check in chanpar email-addresses for this channel
        for row in botslib.query(u'''SELECT chanpar.idpartner_id as idpartner
                                    FROM chanpar,channel,partner
                                    WHERE chanpar.idchannel_id=channel.idchannel
                                    AND chanpar.idpartner_id=partner.idpartner
                                    AND partner.active=%(active)s
                                    AND chanpar.idchannel_id=%(idchannel)s
                                    AND LOWER(chanpar.mail)=%(mail)s''',
                                    {'active':True,'idchannel':self.channeldict['idchannel'],'mail':mailaddress_lower}):
            return row['idpartner']
        #if not found, check in partner-tabel (is less specific). Also test if in CC field.
        for row in botslib.query(u'''SELECT idpartner
                                    FROM partner
                                    WHERE active=%(active)s
                                    AND ( LOWER(mail) = %(mail)s OR LOWER(cc) LIKE %(maillike)s )''',
                                    {'active':True,'mail':mailaddress_lower,'maillike': '%' + mailaddress_lower + '%'}):
            return row['idpartner']
        return None     #indicate email address is unknown


    def idpartner2mailaddress(self,idpartner):
        for row in botslib.query(u'''SELECT chanpar.mail as mail,chanpar.cc as cc
                                    FROM chanpar,channel,partner
                                    WHERE chanpar.idchannel_id=channel.idchannel
                                    AND chanpar.idpartner_id=partner.idpartner
                                    AND partner.active=%(active)s
                                    AND chanpar.idchannel_id=%(idchannel)s
                                    AND chanpar.idpartner_id=%(idpartner)s''',
                                    {'active':True,'idchannel':self.channeldict['idchannel'],'idpartner':idpartner}):
            if row['mail']:
                return row['mail'],row['cc']
        for row in botslib.query(u'''SELECT mail,cc
                                    FROM partner
                                    WHERE active=%(active)s
                                    AND idpartner=%(idpartner)s''',
                                    {'active':True,'idpartner':idpartner}):
            if row['mail']:
                return row['mail'],row['cc']
        raise botslib.CommunicationOutError(_(u'No mail-address for partner "%(partner)s" (channel "%(idchannel)s").'),
                                                {'partner':idpartner,'idchannel':self.channeldict['idchannel']})

    def connect(self):
        pass

    def disconnect(self):
        pass

    @staticmethod
    def convertcodecformime(codec_in):
        convertdict = {
            'ascii' : 'us-ascii',
            'unoa' : 'us-ascii',
            'unob' : 'us-ascii',
            'unoc' : 'iso-8859-1',
            }
        codec_in = codec_in.lower().replace('_','-')
        return convertdict.get(codec_in,codec_in)


    def filename_formatter(self,filename_mask,ta):
        ''' Output filename generation from "template" filename configured in the channel
            Basically python's string.Formatter is used; see http://docs.python.org/library/string.html
            As in string.Formatter, substitution values are surrounded by braces; format specifiers can be used.
            Any ta value can be used
              eg. {botskey}, {alt}, {editype}, {messagetype}, {topartner}
            Next to the value in ta you can use:
            -   * : an unique number (per outchannel) using an asterisk
            -   {datetime}  use datetime with a valid strftime format: 
                eg. {datetime:%Y%m%d}, {datetime:%H%M%S}
            -   {infile} use the original incoming filename; use name and extension, or either part separately:
                eg. {infile}, {infile:name}, {infile:ext}
            -   {overwrite}  if file wit hfielname exists: overwrite it (instead of appending)
            
            Exampels of usage:
                {botskey}_*.idoc        use incoming order number, add unique number, use extension '.idoc'
                *_{infile}              passthrough incoming filename & extension, prepend with unique number
                {infile:name}_*.txt     passthrough incoming filename, add unique number but change extension to .txt
                {editype}-{messagetype}-{datetime:%Y%m%d}-*.{infile:ext}
                                        use editype, messagetype, date and unique number with extension from the incoming file
                {topartner}/{messagetype}/*.edi
                                        Usage of subdirectories in the filename, they must already exist. In the example:
                                        sort into folders by partner and messagetype.
                        
            Note1: {botskey} can only be used if merge is False for that messagetype
        '''
        class infilestr(str):
            ''' class for the infile-string that handles the specific format-options'''
            def __format__(self, format_spec):
                if not format_spec:
                    return unicode(self)
                name,ext = os.path.splitext(unicode(self))
                if format_spec == 'ext':
                    if ext.startswith('.'):
                        ext = ext[1:]
                    return ext 
                if format_spec == 'name':
                    return name 
                raise botslib.CommunicationOutError(_(u'Error in format of "{filename}": unknown format: "%(format)s".'),
                                                    {'format':format_spec})
        unique = unicode(botslib.unique(self.channeldict['idchannel'])) #create unique part for attachment-filename
        tofilename = filename_mask.replace('*',unique)           #filename_mask is filename in channel where '*' is replaced by idta
        if '{' in tofilename:    #only for python 2.6/7
            ta.synall()
            if '{infile' in tofilename:
                ta_list = botslib.trace_origin(ta=ta,where={'status':EXTERNIN})
                if ta_list:
                    infilename = infilestr(os.path.basename(ta_list[-1].filename))
                else:
                    infilename = ''
            else:
                infilename = ''
            try:
                if botsglobal.ini.getboolean('acceptance','runacceptancetest',False):
                    datetime_object = datetime.datetime.strptime("2013-01-23 01:23:45", "%Y-%m-%d %H:%M:%S")
                else:
                    datetime_object = datetime.datetime.now()
                tofilename = tofilename.format(infile=infilename,datetime=datetime_object,**ta.__dict__)
            except:
                txt = botslib.txtexc()
                raise botslib.CommunicationOutError(_(u'Error in formatting outgoing filename "%(filename)s". Error: "%(error)s".'),
                                                        {'filename':tofilename,'error':txt})
        if self.userscript and hasattr(self.userscript,'filename'):
            return botslib.runscript(self.userscript,self.scriptname,'filename',channeldict=self.channeldict,filename=tofilename,ta=ta)
        else:
            return tofilename






class ftp(_comsession):
    def connect(self):
        botslib.settimeout(botsglobal.ini.getint('settings','ftptimeout',10))
        self.session = ftplib.FTP()
        self.session.set_debuglevel(botsglobal.ini.getint('settings','ftpdebug',0))   #set debug level (0=no, 1=medium, 2=full debug)
        self.session.set_pasv(not self.channeldict['ftpactive']) #active or passive ftp
        self.session.connect(host=self.channeldict['host'],port=int(self.channeldict['port']))
        self.session.login(user=self.channeldict['username'],passwd=self.channeldict['secret'],acct=self.channeldict['ftpaccount'])
        self.set_cwd()

    def set_cwd(self):
        self.dirpath = self.session.pwd()
        if self.channeldict['path']:
            self.dirpath = posixpath.normpath(posixpath.join(self.dirpath,self.channeldict['path']))
            try:
                self.session.cwd(self.dirpath)           #set right path on ftp-server
            except:
                self.session.mkd(self.dirpath)           #set right path on ftp-server; no nested directories
                self.session.cwd(self.dirpath)           #set right path on ftp-server

    @botslib.log_session
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

    @botslib.log_session
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
        botslib.settimeout(botsglobal.ini.getint('settings','globaltimeout',10))


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
        # setup logging if required
        ftpdebug = botsglobal.ini.getint('settings','ftpdebug',0)
        if ftpdebug > 0:
            log_file = botslib.join(botsglobal.ini.get('directories','logging'),'sftp.log')
            # Convert ftpdebug to paramiko logging level (1=20=info, 2=10=debug)
            paramiko.util.log_to_file(log_file, 30-(ftpdebug*10))

        # Get hostname and port to use
        hostname = self.channeldict['host']
        try:
            port = int(self.channeldict['port'])
        except:
            port = 22 # default port for sftp

        if self.userscript and hasattr(self.userscript,'hostkey'):
            hostkey = botslib.runscript(self.userscript,self.scriptname,'hostkey',channeldict=self.channeldict)
        else:
            hostkey = None
        if self.userscript and hasattr(self.userscript,'privatekey'):
            privatekeyfile,pkeytype,pkeypassword = botslib.runscript(self.userscript,self.scriptname,'privatekey',channeldict=self.channeldict)
            if pkeytype == 'RSA':
                pkey = paramiko.RSAKey.from_private_key_file(filename=privatekeyfile,password=pkeypassword)
            else:
                pkey = paramiko.DSSKey.from_private_key_file(filename=privatekeyfile,password=pkeypassword)
        else:
            pkey = None

        if self.channeldict['secret']:  #if password is empty string: use None. Else error can occur.
            secret = self.channeldict['secret']
        else:
            secret = None
        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        self.transport = paramiko.Transport((hostname,port))
        self.transport.connect(username=self.channeldict['username'],password=secret,hostkey=hostkey,pkey=pkey)
        self.session = paramiko.SFTPClient.from_transport(self.transport)
        channel = self.session.get_channel()
        channel.settimeout(botsglobal.ini.getint('settings','ftptimeout',10))
        self.set_cwd()

    def set_cwd(self):
        self.session.chdir('.') # getcwd does not work without this chdir first!
        self.dirpath = self.session.getcwd()
        if self.channeldict['path']:
            self.dirpath = posixpath.normpath(posixpath.join(self.dirpath,self.channeldict['path']))
            try:
                self.session.chdir(self.dirpath)
            except:
                self.session.mkdir(self.dirpath)
                self.session.chdir(self.dirpath)

    def disconnect(self):
        self.session.close()
        self.transport.close()
        

    @botslib.log_session
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

    @botslib.log_session
    def outcommunicate(self):
        ''' do ftp: send files. To be used via receive-dispatcher.
            each to be send file is transaction.
            each send file is transaction.
        '''
        #get right filename_mask & determine if fixed name (append) or files with unique names
        filename_mask = self.channeldict['filename'] if self.channeldict['filename'] else '*'
        if '{overwrite}' in filename_mask:
            filename_mask = filename_mask.replace('{overwrite}','')
            mode = 'w'
        else:
            mode = 'a'
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
                fromfile = botslib.opendata(row['filename'], 'rb')
                tofile = self.session.open(tofilename, mode)    # SSH treats all files as binary
                tofile.write(fromfile.read())
                tofile.close()
                fromfile.close()
                #Rename filename after writing file.
                #Function: safe file writing: do not want another process to read the file while it is being written.
                if self.channeldict['mdnchannel']:
                    tofilename_old = tofilename
                    tofilename = botslib.rreplace(tofilename_old,self.channeldict['mdnchannel'])
                    self.session.rename(tofilename_old,tofilename)
            except:
                txt = botslib.txtexc()
                ta_to.update(statust=ERROR,errortext=txt,filename='sftp:/'+posixpath.join(self.dirpath,tofilename),numberofresends=row['numberofresends']+1)
            else:
                ta_to.update(statust=DONE,filename='sftp:/'+posixpath.join(self.dirpath,tofilename),numberofresends=row['numberofresends']+1)
            finally:
                ta_from.update(statust=DONE)





            
class edi_route(models.Model):
    _inherit = 'edi.route' 
    
    ftp_host = fields.Char(string="Host",required=True)
    ftp_user = fields.Char(string="User",required=True)
    ftp_password = fields.Char(string="Password",required=True)
    ftp_directory = fields.Char(string="Directory",required=True)

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
    def get_file(self):
        pass
        
    @api.one
    def put_file(self,file):
        pass

        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
