from bots.botsconfig import *
from envelope import recorddefs,structure,nextmessage,nextmessage2

syntax = { 
        'version'    :  '2',	    #for outgong: value to use in UNB
        'envelope'   :  'edifact',	#for outgoing edifact-messages: this is the envelope to use in merge()
        'charset'   :  'UNOC',	#for outgoing edifact-messages: this is the envelope to use in merge()
        }
