import fnmatch
import posixpath
from bots.botsconfig import *

import bots.botslib as botslib
import bots.communication as communication


class UserCommunicationClass(communication.ftp):
    @botslib.log_session
    def incommunicate(self):
        ''' subclassing ftp for Posten.
            Posten has 1 file for receiving edi files; after the file is fetched, the ' next'  edifile (same name..) is available, untill all are read
        '''
        while(1):
            try:
                lijst = fnmatch.filter(self.session.nlst(),self.channeldict['filename'])
                if lijst:
                    fromfilename = lijst[0]
                else:
                    break   #no 'new' edi files anymore
                ta_from = botslib.NewTransaction(filename='ftp:/'+posixpath.join(self.dirpath,fromfilename),
                                                    status=EXTERNIN,
                                                    fromchannel=self.channeldict['idchannel'],
                                                    charset=self.channeldict['charset'],idroute=self.idroute)
                ta_to = ta_from.copyta(status=RAWIN)
                tofilename = str(ta_to.idta)
                if self.channeldict['ftpbinary']:
                    tofile = botslib.opendata(tofilename, 'wb')
                    self.session.retrbinary("RETR " + fromfilename, tofile.write)
                else:
                    tofile = botslib.opendata(tofilename, 'w')
                    self.session.retrlines("RETR " + fromfilename, lambda s, w=tofile.write: w(s+"\n"))
                tofile.close()
                if self.channeldict['remove']:
                    self.session.delete(fromfilename)
            except:
                txt=botslib.txtexc()
                botslib.ErrorProcess(functionname='ftp-incommunicate',errortext=txt)
                #~ ta_from.update(statust=ERROR,errortext=txt)  #this has the big advantage it will be retried again!
                ta_from.delete()
                ta_to.delete()    #is not received
            else:
                ta_from.update(statust=DONE)
                ta_to.update(filename=tofilename,statust=OK)
                
