#mapping-script

def main(inn,out):
    out.put({'BOTSID':'HEA','EANSENDER':inn.ta_info['frompartner']})
    out.put({'BOTSID':'HEA','EANRECEIVER':inn.ta_info['topartner']})
    out.put({'BOTSID':'HEA','TEST':inn.ta_info['testindicator']})
    out.put({'BOTSID':'HEA','MESSAGETYPE':'orders01'})
    out.put({'BOTSID':'HEA','ORDERNUMBER':inn.get({'BOTSID':'UNH'},{'BOTSID':'RFF','C506.1153':'CR','C506.1154':None})})
    out.put({'BOTSID':'HEA','ORDERDATE':inn.get({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'137','C507.2380':None})})
    out.put({'BOTSID':'HEA','DELDATESTORE':inn.get({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'2','C507.2380':None})})
    out.put({'BOTSID':'HEA','DELDATELE':inn.get({'BOTSID':'UNH'},{'BOTSID':'DTM','C507.2005':'69','C507.2380':None})})
    
    out.put({'BOTSID':'HEA','EANBUYER':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'BY','C082.3039':None})})
    out.put({'BOTSID':'HEA','BUYER_ORGID':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'BY'},{'BOTSID':'RFF','C506.1153':'GN','C506.1154':None})})
    out.put({'BOTSID':'HEA','BUYER_VATNR':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'BY'},{'BOTSID':'RFF','C506.1153':'VA','C506.1154':None})})
    out.put({'BOTSID':'HEA','EANSUPPLIER':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SU','C082.3039':None})})
    out.put({'BOTSID':'HEA','EANDELIVERY':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'DP','C082.3039':None})})
    out.put({'BOTSID':'HEA','EANCONSIGNEE':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'CN','C082.3039':None})})
    out.put({'BOTSID':'HEA','EANSHOP':inn.get({'BOTSID':'UNH'},{'BOTSID':'NAD','3035':'SN','C082.3039':None})})
    
    out.put({'BOTSID':'HEA','SHIPDATEFROMLE':inn.get({'BOTSID':'UNH'},{'BOTSID':'FTX','4451':'MKS','C108.4440#1':None})})
    out.put({'BOTSID':'HEA','FREIGHTLABEL1':inn.get({'BOTSID':'UNH'},{'BOTSID':'FTX','4451':'MKS','C108.4440#2':None})})
    out.put({'BOTSID':'HEA','FREIGHTLABEL2':inn.get({'BOTSID':'UNH'},{'BOTSID':'FTX','4451':'MKS','C108.4440#3':None})})
    out.put({'BOTSID':'HEA','CUSTOMERNUMBER':inn.get({'BOTSID':'UNH'},{'BOTSID':'FTX','4451':'MKS','C108.4440#4':None})})
    out.put({'BOTSID':'HEA','CUSTOMERNAME':inn.get({'BOTSID':'UNH'},{'BOTSID':'FTX','4451':'MKS','C108.4440#5':None})})
    out.put({'BOTSID':'HEA','DISTRIBUTION':inn.get({'BOTSID':'UNH'},{'BOTSID':'FTX','4451':'DEL','C108.4440#1':None})})

    for lin in inn.getloop({'BOTSID':'UNH'},{'BOTSID':'LIN'}):
        lou = out.putloop({'BOTSID':'HEA'},{'BOTSID':'LIN'})
        lou.put({'BOTSID':'LIN','NUMBER':lin.get({'BOTSID':'LIN','1082':None})})
        lou.put({'BOTSID':'LIN','EAN':lin.get({'BOTSID':'LIN','C212.7140':None})})
        lou.put({'BOTSID':'LIN','SU_ARTICLECODE':lin.get({'BOTSID':'LIN'},{'BOTSID':'PIA','4347':'5','C212#1.7143':'SA','C212#1.7140':None})})
        lou.put({'BOTSID':'LIN','QTY_ORDERED':lin.get({'BOTSID':'LIN'},{'BOTSID':'QTY','C186.6063':'21','C186.6060':None})})
        lou.put({'BOTSID':'LIN','IND_MARKPRICE':lin.get({'BOTSID':'LIN'},{'BOTSID':'FTX','4451':'ZZZ','C108.4440#1':None})})
        lou.put({'BOTSID':'LIN','CONPRICE':lin.get({'BOTSID':'LIN'},{'BOTSID':'PRI','C509.5125':'AAB','C509.5387':'RPT','C509.5118':None})})
