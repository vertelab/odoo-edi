from bots.botsconfig import *


structure=    [
    {ID:'HEA',MIN:1,MAX:10000,LEVEL:[
        {ID:'LIN',MIN:0,MAX:10000},
        ]},
    ]
    

recorddefs = {
'HEA':[
        ['BOTSID','M',3,'A'],
        ['MESSAGETYPE', 'C', 20, 'AN'],      #messagetype ID: order01
        ['EANSENDER', 'C', 13, 'AN'],        #ILN sender; is the ILN of ICA headquarter
        ['EANRECEIVER', 'C', 13, 'AN'],      #ILN reciever; is the same as ILN supplier
        ['TEST', 'C', 1, 'AN'],              #indicates test or not (1=test)
        ['ORDERNUMBER', 'C', 17, 'AN'],      #Order number, used in ORDRSP, DESADV.
        ['ORDERDATE', 'C', 12, 'AN'],        #date order is created. Format: CCYYMMDD
        ['DELDATESTORE', 'C', 12, 'AN'],     #Desired date of delivery to stores. Format: CCYYMMDD. This date has to be used in order response and despatch advice!
        ['DELDATELE', 'C', 12, 'AN'],        #Expedition Date / Lovat date of delivery to the ICA's storage unit. Format: CCYYMMDD
        ['SHIPDATEFROMLE', 'C', 12, 'AN'],   #Utleveransdag from ICA. Format: CCYYMMDD
        ['EANBUYER', 'C', 13, 'AN'],         #ILN Buyer (LE of ICA)
        ['BUYER_ORGID', 'C', 13, 'AN'],      #Organizations-No. buyer
        ['BUYER_VATNR', 'C', 13, 'AN'],      #Momsregistreringsnummert buyer
        ['EANSUPPLIER', 'C', 13, 'AN'],      #ILN Supplier
        ['EANDELIVERY', 'C', 13, 'AN'],      #ILN primary deliverey place (LE)
        ['EANCONSIGNEE', 'C', 13, 'AN'],     #ILN Consignee - the ICA LE
        ['EANSHOP', 'C', 13, 'AN'],          #ILN shop number
        ['CUSTOMERNUMBER', 'C', 17, 'AN'],   #The shop's customer number at the ICA (n. .5)
        ['CUSTOMERNAME', 'C', 17, 'AN'],     #Customer name an .. 20   Did not see this in the example.
        ['FREIGHTLABEL1', 'C', 70, 'AN'],    #Freight Labeling of primary-LE: Utlev. Area / Port / class / Waiting in car / Off box / In-box (an2/an2/an3/an2/an3/an3) 
        ['FREIGHTLABEL2', 'C', 70, 'AN'],    #Freight Labeling of secondary-LE: Utlev. Area / Port / class / Waiting in car / Off box / In-box (an2/an2/an3/an2/an3/an3). Did not see this in the example.
        ['DISTRIBUTION', 'C', 3, 'AN'],       #ICA = ICA distributes, LEV = Vendor distributes 
      ],
'LIN':[
        ['BOTSID','M',3,'A'],
        ['NUMBER', 'C', 6, 'N'],             #line number
        ['EAN', 'C', 14, 'AN'],              #article EAN 
        ['SU_ARTICLECODE', 'C', 14, 'AN'],   #supplier article number
        ['QTY_ORDERED', 'C', 18, 'N'],     #quantity ordered
        ['IND_MARKPRICE', 'C', 35, 'AN'],    #J = Prismarkning, N = Ingen Prismarkning
        ['CONPRICE', 'C', 18, 'N'],       # Consumer Price (for Prismarkning) 
      ],
    }
     
