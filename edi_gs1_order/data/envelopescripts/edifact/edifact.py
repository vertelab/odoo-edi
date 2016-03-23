
def ta_infocontent(ta_info):
    conv0026 = {'ORDRSPD93AUNEDIT30':'ICARSP3',
                'DESADVD93AUNEDIT30':'ICADAD3',
                'INVOICD93AUNEDIT30':'ICAINV3',
                }
    ta_info['UNB.0026'] = conv0026.get(ta_info.get('messagetype',''),'')
