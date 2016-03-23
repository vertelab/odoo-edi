import xmlrpclib
import datetime
import bots.botslib as botslib
import bots.communication as communication
from bots.botsconfig import *


class UserCommunicationClass(communication.xmlrpc):
    #***************************************************
    #constants used in OpenERP xml-rpc interface for green vision
    username = 'bots'
    pwd = 'aHR7G;NovX7'
    dbname = 'greenvision'
    loginpath = 'xmlrpc/common'
    loginfile = 'login'
    rpcfunction = 'execute'
    #***************************************************
    def connect(self):
        ''' first login, get the uid. '''
        loginuri = botslib.Uri(scheme=self.scheme,host=self.channeldict['host'],port=self.channeldict['port'],path=self.loginpath)
        loginsession = xmlrpclib.ServerProxy(loginuri.uri)
        tocall = getattr(loginsession,self.loginfile)
        self.uid = tocall(self.dbname, self.username, self.pwd)
        
        self.uri = botslib.Uri(scheme=self.scheme,host=self.channeldict['host'],port=self.channeldict['port'],path=self.channeldict['path'])
        self.session =  xmlrpclib.ServerProxy(self.uri.uri,use_datetime=True)


    @botslib.log_session
    def incommunicate(self):
        ''' receive files over XML-RPC.'''
        # c=confirmed order in OpenERP  d =Delivered order to BOTS u = Unconfirmed order in OpenERP
        tocall = getattr(self.session,self.rpcfunction)
        
        #~ message_ids = tocall(self.dbname, self.uid, self.pwd, self.channeldict['filename'],'search',[('status','=','d')])  
        #~ for message_id in message_ids:
            #~ print 'put back' ,self.channeldict['filename']
            #~ ordrsp_delivered = tocall(self.dbname, self.uid, self.pwd, self.channeldict['filename'], 'write',[message_id], {'status': 'c'})
        #~ return
        message_ids = tocall(self.dbname, self.uid, self.pwd, self.channeldict['filename'],'search',[('status','=','c')])  
        for message_id in message_ids:
            try:
                ta_from = botslib.NewTransaction(filename=self.uri.update(filename=str(message_id)),
                                                    status=EXTERNIN,
                                                    fromchannel=self.channeldict['idchannel'],
                                                    charset=self.channeldict['charset'],idroute=self.idroute)
                ta_to =   ta_from.copyta(status=RAWIN)
                
                rpcmessage = tocall(self.dbname, self.uid, self.pwd, self.channeldict['filename'], 'read', [message_id])
                # Confirm/change status ordrsp to OpenERP
                ordrsp_delivered = tocall(self.dbname, self.uid, self.pwd, self.channeldict['filename'], 'write',[message_id], {'status': 'd'})
                #~ print 'received message',self.channeldict['filename']
                tofilename = str(ta_to.idta)
                tofile = botslib.opendata(tofilename, 'wb')
                tofile.write(rpcmessage[0]['blob'])
                tofile.close()
            except:
                txt=botslib.txtexc()
                botslib.ErrorProcess(functionname='xmlprc-incommunicate',errortext=txt)
                ta_from.delete()
                ta_to.delete()    #is not received
            else:
                ta_from.update(statust=DONE)
                ta_to.update(filename=tofilename,statust=OK)
    
    @botslib.log_session
    def outcommunicate(self):
        ''' send files over XML-RPC.'''
        openerptime = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
        tocall = getattr(self.session,self.rpcfunction)
        for idta,fromfilename,charset,editype in botslib.query('''SELECT idta,filename,charset,editype
                                    FROM ta
                                    WHERE tochannel=%(tochannel)s
                                      AND status=%(status)s
                                      AND statust=%(statust)s
                                      AND idta>%(rootidta)s
                                        ''',
                                    {'tochannel':self.channeldict['idchannel'],'rootidta':botslib.get_minta4query(),
                                    'status':RAWOUT,'statust':OK}):
            try:
                ta_from = botslib.OldTransaction(idta)
                ta_to =   ta_from.copyta(status=EXTERNOUT)
                fromfile = botslib.opendata(fromfilename, 'rb',charset)
                content = fromfile.read()
                fromfile.close()
                filename = tocall(self.dbname, self.uid, self.pwd, self.channeldict['filename'],'create',{'date': openerptime,'blob':content})
            except:
                txt=botslib.txtexc()
                ta_to.update(statust=ERROR,errortext=txt)
            else:
                ta_from.update(statust=DONE)
                ta_to.update(statust=DONE,filename=self.uri.update(filename=str(filename)))
