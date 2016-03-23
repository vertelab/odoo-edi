#mapping-script
import time
def empt(value):
    if value:
        return value
    else:
        return None

def main(inn,out):
    out.ta_info['topartner'] = '7301002000009'
    out.put({'BOTSID':'UNH','0062':out.ta_info['reference'],'S009.0065':'INVOIC','S009.0052':'D','S009.0054':'93A','S009.0051':'UN','S009.0057':'EDIT30'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'BGM','C002.1001':'380','1004':empt(inn.get({'BOTSID':'HEA','INVOICENUMBER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'50','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','DELDATE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'35','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','INVOICEDATE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'RFF','C506.1153':'CS','C506.1154':empt(inn.get({'BOTSID':'HEA','DISTRIBUTION':None}))})
    
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'BY','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANBUYER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'CN','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANCONSIGNEE':None}))})
    if out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SU','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANSUPPLIER':None}))}):
        out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SU'},{'BOTSID':'RFF','C506.1153':'VA','C506.1154':empt(inn.get({'BOTSID':'HEA','SUPPLIER_VATNR':None}))})
        out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SU'},{'BOTSID':'RFF','C506.1153':'GN','C506.1154':empt(inn.get({'BOTSID':'HEA','SUPPLIER_ORGID':None}))})
        
    out.put({'BOTSID':'UNH'},{'BOTSID':'PAT','4279':'3','C112.2475':'6'},{'BOTSID':'DTM','C507.2005':'13','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','DUEDATE':None}))})
    #~ out.put({'BOTSID':'UNH'},{'BOTSID':'PAT','4279':'22','C112.2475':'6'},{'BOTSID':'DTM','C507.2005':'12','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','DUEDATE':None}))})
    
    out.put({'BOTSID':'UNH'},{'BOTSID':'ALC','5463':'C','4471':'2','C214.7161':'IS'},{'BOTSID':'MOA','C516.5025':'23','C516.5004':empt(inn.getnozero({'BOTSID':'HEA','TOT_CHARGE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'ALC','5463':'A','4471':'2','C214.7161':'DI'},{'BOTSID':'MOA','C516.5025':'204','C516.5004':empt(inn.getnozero({'BOTSID':'HEA','TOT_DISCOUNT':None}))})

    for lin in inn.getloop({'BOTSID':'HEA'},{'BOTSID':'LIN'}):
        lou = out.putloop({'BOTSID':'UNH'},{'BOTSID':'LIN'})
        lou.put({'BOTSID':'LIN','1082':empt(lin.get({'BOTSID':'LIN','NUMBER':None}))})
        lou.put({'BOTSID':'LIN','C212.7143':'EN','C212.7140':empt(lin.get({'BOTSID':'LIN','EAN':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PIA','4347':'5','C212#1.7143':'SA','C212#1.7140':empt(lin.get({'BOTSID':'LIN','SU_ARTICLECODE':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'QTY','C186.6063':'47','C186.6411':'PCE','C186.6060':empt(lin.get({'BOTSID':'LIN','QTY_INVOICED':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'MOA','C516.5025':'203','C516.5004':empt(lin.get({'BOTSID':'LIN','LINE_NET':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PRI','C509.5125':'AAB','C509.5118':empt(lin.get({'BOTSID':'LIN','LISTPRICE':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'TAX','5283':'7','C241.5153':'VAT','5305':'S','C243.5278':empt(lin.get({'BOTSID':'LIN','TAXPERCENTAGE':None}))})
        
        lou.put({'BOTSID':'LIN'},{'BOTSID':'ALC','5463':'C','4471':'2','C214.7161':'IS'},{'BOTSID':'MOA','C516.5025':'23','C516.5004':empt(lin.getnozero({'BOTSID':'LIN','LIN_CHARGE':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'ALC','5463':'A','4471':'2','C214.7161':'DI'},{'BOTSID':'MOA','C516.5025':'204','C516.5004':empt(lin.getnozero({'BOTSID':'LIN','LIN_DISCOUNT':None}))})

    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS','0081':'S'})
    numberoflines = out.getcountoccurrences({'BOTSID':'UNH'},{'BOTSID':'LIN'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'CNT','C270.6069':'2','C270.6066':numberoflines})
    
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'MOA','C516.5025':'9','C516.5004':empt(inn.get({'BOTSID':'HEA','TOTALINVOIC':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'MOA','C516.5025':'79','C516.5004':empt(inn.get({'BOTSID':'HEA','TOTALLINE_NET':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'MOA','C516.5025':'125','C516.5004':empt(inn.get({'BOTSID':'HEA','TOTALTAXABLE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'MOA','C516.5025':'129','C516.5004':empt(inn.getnozero({'BOTSID':'HEA','SUBJECTPAYDISC':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'MOA','C516.5025':'176','C516.5004':empt(inn.getnozero({'BOTSID':'HEA','TOTALTAX':None}))})
    for count in range(1,3):
        TAXAMOUNT = empt(inn.getnozero({'BOTSID':'HEA','TAXAMOUNT%s'%count:None}))
        if TAXAMOUNT:
            tax = out.putloop({'BOTSID':'UNH'},{'BOTSID':'UNS'},{'BOTSID':'TAX'})
            tax.put({'BOTSID':'TAX','5283':'7','C241.5153':'VAT','5305':'S','C243.5278':empt(inn.get({'BOTSID':'HEA','TAXPERCENTAGE%s'%count:None}))})
            tax.put({'BOTSID':'TAX'},{'BOTSID':'MOA','C516.5025':'176','C516.5004':TAXAMOUNT})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNT','0074':out.getcount()+1,'0062':out.ta_info['reference']})
