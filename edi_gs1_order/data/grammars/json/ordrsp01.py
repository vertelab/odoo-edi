from bots.botsconfig import *


structure=    [
    {ID:'HEA',MIN:1,MAX:10000,
        QUERIES:{
       'frompartner':  {'BOTSID':'HEA','EANSENDER':None},
        'topartner':    {'BOTSID':'HEA','EANRECEIVER':None},
        'reference':    {'BOTSID':'HEA','ORDERRESNUMBER':None},
        'testindicator':{'BOTSID':'HEA','TEST':None}
        },
        LEVEL:[
        {ID:'LIN',MIN:0,MAX:10000},
        ]},
    ]
    

recorddefs = {
'HEA':[
        ['BOTSID','M',3,'A'],
        ['MESSAGETYPE', 'C', 20, 'AN'],      #messagetype ID: ordrsp01
        ['EANSENDER', 'C', 13, 'AN'],        #ILN sender; is the same as ILN supplier
        ['EANRECEIVER', 'C', 13, 'AN'],      #ILN reciever; is the ILN of ICA headquarter
        ['TEST', 'C', 1, 'AN'],              #indicates test or not (1=test)
        ['ORDERRESNUMBER', 'C', 17, 'AN'],   #order response number: not used for referencing
        ['ORDERNUMBER', 'C', 17, 'AN'],      #as in order (ICA ordernumber)
        ['ORDERRESDATE', 'C', 12, 'AN'],     #date order response is created. Format: CCYYMMDD
        ['DELDATESTORE', 'C', 12, 'AN'],     #Desired date of delivery to stores. Format: CCYYMMDD
        ['DELDATELE', 'C', 12, 'AN'],        #Confirmed, promised delivery date to the ICA's storage unit. Format: CCYYMMDD
        ['EANBUYER', 'C', 13, 'AN'],         #ILN Buyer (LE of ICA)
        ['EANSUPPLIER', 'C', 13, 'AN'],      #ILN Supplier
        ['EANCONSIGNEE', 'C', 13, 'AN'],     #Consignee, LE of ICA (or store, on Sped-delivery.)
        ['EANSHOP', 'C', 13, 'AN'],          #ILN shop number
        ['CUSTOMERNUMBER', 'C', 17, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #patch bad ordrsp in test
        #~ ['BUYER_ORGID', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['FREIGHTLABEL1', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['FREIGHTLABEL2', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['BUYER_VATNR', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['SHIPDATEFROMLE', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['DISTRIBUTION', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['BUYER_VATNR', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['EANDELIVERY', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
        #~ ['ORDERDATE', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
      ],
'LIN':[
        ['BOTSID','M',3,'A'],
        ['NUMBER', 'C', 6, 'N'],             #line number
        ['EAN', 'C', 14, 'AN'],              #article EAN 
        ['SU_ARTICLECODE', 'C', 14, 'AN'],   #supplier article number
        ['QTY_ORDERED', 'C', 18, 'R'],       #quantity ordered (same quantity as in the order)
        ['QTY_AVAILABLE', 'C', 18, 'R'],     #quantity to to be delivered; if zero this should be '0'
        ['NETPRICE', 'C', 18, 'R'],          # net price of article*********no examples. is this used?
        #patch bad ordrsp in test
        #~ ['IND_MARKPRICE', 'C', 70, 'AN'],   #The shop's customer number at the ICA (n. .5)
      ],
    }
 