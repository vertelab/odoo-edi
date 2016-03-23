#mapping-script

def empt(value):
    if value:
        return value
    else:
        return None

def main(inn,out):
    out.ta_info['topartner'] = '7301002000009'
    out.put({'BOTSID':'UNH','0062':out.ta_info['reference'],'S009.0065':'DESADV','S009.0052':'D','S009.0054':'93A','S009.0051':'UN','S009.0057':'EDIT30'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'BGM','1004':empt(inn.get({'BOTSID':'HEA','DESADVNUMBER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'BGM','C002.1001':'351','1225':'9'})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'137','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','DESADVDATE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'132','C507.2379':'102','C507.2380':empt(inn.get({'BOTSID':'HEA','ESTDELDATE':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'RFF','C506.1153':'AAS','C506.1154':empt(inn.get({'BOTSID':'HEA','TRANSPORTNUMBER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'BY','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANBUYER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SH','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANSHIPPER':None}))})
    out.put({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'DP','C082.3055':'9','C082.3039':empt(inn.get({'BOTSID':'HEA','EANDELIVERY':None}))})
    
    for regel in inn.getloop({'BOTSID':'HEA'},{'BOTSID':'PAC'}):
        lou = out.putloop({'BOTSID':'UNH'},{'BOTSID':'CPS'})
        lou.put({'BOTSID':'CPS','7166':'1','7164':empt(regel.get({'BOTSID':'PAC','PACNUMBER':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'PAC','7224': '1'})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'PAC','C202.7065':empt(regel.get({'BOTSID':'PAC','TYPEOFPACKAGES':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'PAC'},{'BOTSID':'PCI','4233':'30E'})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'PAC'},{'BOTSID':'PCI'},{'BOTSID':'GIN','7405':'SS','C208#1.7402#1':empt(regel.get({'BOTSID':'PAC','SSCC':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'LIN','1082':'1'})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'LIN'},{'BOTSID':'RFF','C506.1153':'CR','C506.1154':empt(regel.get({'BOTSID':'PAC','ORDERNUMBER':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'LIN'},{'BOTSID':'LOC','3227':'83','C517.3055':'9','C517.3225':empt(regel.get({'BOTSID':'PAC','EANCONSIGNEE':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'LIN'},{'BOTSID':'LOC','3227':'7','C517.3055':'9','C517.3225':empt(regel.get({'BOTSID':'PAC','EANSHOP':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'LIN'},{'BOTSID':'LOC','3227':'7','C517.3055':'9','C517.3224':empt(regel.get({'BOTSID':'PAC','CUSTOMERNUMBER':None}))})
        lou.put({'BOTSID':'CPS'},{'BOTSID':'LIN'},{'BOTSID':'LOC','3227':'7','C517.3055':'9'},{'BOTSID':'DTM','C507.2005':'2','C507.2379':'102','C507.2380':empt(regel.get({'BOTSID':'PAC','DELDATESHOP':None}))})
        
    out.put({'BOTSID':'UNH'},{'BOTSID':'UNT','0074':out.getcount()+1,'0062':out.ta_info['reference']})  #last line (counts the segments produced in out-out
