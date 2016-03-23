#mapping-script
import time

def empt(value):
    if value:
        return value
    else:
        return None

def main(inn,out):
    out.ta_info['topartner'] = '7301002000009'
    out.put({'BOTSID':'UNH','0062':out.ta_info['reference'],'S009.0065':'ORDRSP','S009.0052':'D','S009.0054':'93A','S009.0051':'UN','S009.0057':'EDIT30'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'BGM','1004':empt(inn.get({'BOTSID':'HEA','ORDERRESNUMBER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'BGM','C002.1001':'231','1225':'9'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'137','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','ORDERRESDATE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'69','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','DELDATELE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'2','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','DELDATESTORE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'RFF','C506.1153':'ON','C506.1154':empt(inn.get({'BOTSID':'HEA','ORDERNUMBER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'BY','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANBUYER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SU','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANSUPPLIER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'CN','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANCONSIGNEE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SN','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANSHOP':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SN'},{'BOTSID':'RFF','C506.1153':'API','C506.1154':empt(inn.get({'BOTSID':'HEA','CUSTOMERNUMBER':None}))})
    
    for regel in inn.getloop({'BOTSID':'HEA'},{'BOTSID':'LIN'}):
        lou = out.putloop({'BOTSID':'UNH'},{'BOTSID':'LIN'})
        lou.put({'BOTSID':'LIN','1082':empt(regel.get({'BOTSID':'LIN','NUMBER':None}))})
        lou.put({'BOTSID':'LIN','C212.7143':'EN','C212.7140':empt(regel.get({'BOTSID':'LIN','EAN':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PIA','4347':'1','C212#1.7143':'NB','C212#1.7140':empt(regel.get({'BOTSID':'LIN','BATCHNUMBER':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PIA','4347':'5','C212#1.7143':'SA','C212#1.7140':empt(regel.get({'BOTSID':'LIN','SU_ARTICLECODE':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PIA','4347':'2','C212#1.7143':'SA','C212#1.7140':empt(regel.get({'BOTSID':'LIN','SU_ARTICLECODESUBS':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PIA','4347':'3','C212#1.7143':'A','C212#1.7140':empt(regel.get({'BOTSID':'LIN','SU_ARTICLECODESUBS':None}))})

        lou.put({'BOTSID':'LIN'},{'BOTSID':'QTY','C186.6063':'21','C186.6411':'PCE','C186.6060':empt(regel.get({'BOTSID':'LIN','QTY_ORDERED':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'QTY','C186.6063':'17','C186.6411':'PCE','C186.6060':empt(regel.get({'BOTSID':'LIN','QTY_AVAILABLE':None}))})

#        lou.put({'BOTSID':'LIN'},{'BOTSID':'QTY','C186.6063':'21','C186.6060':empt(regel.get({'BOTSID':'LIN','QTY_ORDERED':None}))})
#        lou.put({'BOTSID':'LIN'},{'BOTSID':'QTY','C186.6063':'17','C186.6060':empt(regel.get({'BOTSID':'LIN','QTY_AVAILABLE':None}))})
        lou.put({'BOTSID':'LIN'},{'BOTSID':'PRI','C509.5125':'AAA','C509.5118':empt(regel.get({'BOTSID':'LIN','NETPRICE':None}))})

    out.put({'BOTSID':'UNH'},{'BOTSID':'UNS','0081':'S'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNT','0074':out.getcount()+1,'0062':out.ta_info['reference']})  #last line (counts the segments produced in out-out
