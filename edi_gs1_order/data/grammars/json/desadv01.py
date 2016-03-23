from bots.botsconfig import *


structure=    [
    {ID:'HEA',MIN:1,MAX:10000,
        QUERIES:{
            'frompartner':  {'BOTSID':'HEA','EANSENDER':None},
            'topartner':    {'BOTSID':'HEA','EANRECEIVER':None},
            'reference':    {'BOTSID':'HEA','DESADVNUMBER':None},
            'testindicator':{'BOTSID':'HEA','TEST':None}},
        LEVEL:[
            {ID:'PAC',MIN:0,MAX:10000},
            ]},
    ]
    
nextmessage = ({'BOTSID':'HEA'},)

recorddefs = {
'HEA':[
        ['BOTSID','M',3,'A'],
        ['MESSAGETYPE', 'C', 20, 'AN'],      #messagetype ID: desadv01
        ['EANSENDER', 'C', 13, 'AN'],        #ILN sender; is the same as ILN supplier
        ['EANRECEIVER', 'C', 13, 'AN'],      #ILN reciever; is the ILN of ICA headquarter
        ['TEST', 'C', 1, 'AN'],              #indicates test or not (1=test)
        ['DESADVNUMBER', 'C', 17, 'AN'],     #despatch advice number
        ['DESADVDATE', 'C', 12, 'AN'],       #date despatch advice is created. Format: CCYYMMDD
        ['ESTDELDATE', 'C', 12, 'AN'],       #Estimated date of delivery. Format: CCYYMMDD
        ['TRANSPORTNUMBER', 'C', 17, 'AN'],  # Transport document number/A unique number identifying the load. Might be the same as the despatch advice number
        ['EANBUYER', 'C', 13, 'AN'],         #ILN Buyer (LE of ICA)
        ['EANSHIPPER', 'C', 13, 'AN'],       #ILN Shipper (is ILN supplier)
        ['EANDELIVERY', 'C', 13, 'AN'],      #ILN primary delivey place (LE)
      ],
#~ Per package. The articles in a packages are not described!
'PAC':[
        ['BOTSID','M',3,'A'],
        ['PACNUMBER', 'C', 6, 'N'],          #packages counter (1,2,3 etc). 
        ['TYPEOFPACKAGES', 'C', 7, 'AN'],     #type of package: identification code of the returnable box. Specific code list.
        ['SSCC', 'C', 18, 'AN'],             #SS = lastbararidentitet (EANs Serial Shipping Container Code); unique identification of the packages; is barcoded on the packages.
        ['ORDERNUMBER', 'C', 17, 'AN'],      #The order number assigned by the ICA for the effective management of logistics kejdjan. 
        ['EANCONSIGNEE', 'C', 13, 'AN'],     #ILN of LE
        ['EANSHOP', 'C', 13, 'AN'],          #ILN shop number
        ['CUSTOMERNUMBER', 'C', 37, 'AN'],   #The shop's customer number at the ICA (n. .5)
        ['DELDATESHOP', 'C', 12, 'AN'],      #date of delivery of goods to the store. Stating the date is in order from the ICA. Format: CCYYMMDD. This date is mentioned in the order.
      ],
    }
     
