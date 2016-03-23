from bots.botsconfig import *


structure=    [
{ID:'HEA',MIN:1,MAX:10000,
    QUERIES:{
        'frompartner':  {'BOTSID':'HEA','EANSENDER':None},
        'topartner':    {'BOTSID':'HEA','EANRECEIVER':None},
        'reference':    {'BOTSID':'HEA','INVOICENUMBER':None},
        'testindicator':{'BOTSID':'HEA','TEST':None}},
    LEVEL:[
        {ID:'LIN',MIN:0,MAX:10000},
        ]},
]

nextmessage = ({'BOTSID':'HEA'},)

    
recorddefs = {
'HEA':[
        ['BOTSID','M',3,'A'],
        ['MESSAGETYPE', 'C', 20, 'AN'],      #messagetype ID
        ['EANSENDER', 'C', 13, 'AN'],        #ILN sender; is the same as ILN supplier
        ['EANRECEIVER', 'C', 13, 'AN'],      #ILN reciever; is the ILN of ICA headquarter
        ['TEST', 'C', 1, 'AN'],              #indicates test or not (1=test)
        ['INVOICENUMBER', 'C', 17, 'AN'],    #invoice number
        ['INVOICEDATE', 'C', 12, 'AN'],      #invoice date. Format: CCYYMMDD
        ['DELDATE', 'C', 12, 'AN'],          #delivery date at ICA. Is very important for ICA! Format: CCYYMMDD
        ['EANBUYER', 'C', 13, 'AN'],         #ILN Buyer (LE of ICA)
        ['EANSUPPLIER', 'C', 13, 'AN'],      #ILN Supplier
        ['SUPPLIER_ORGID', 'C', 13, 'AN'],   #Organizations-No. Supplier
        ['SUPPLIER_VATNR', 'C', 17, 'AN'],   #Momsregistreringsnummert Supplier
        ['EANCONSIGNEE', 'C', 13, 'AN'],     #ILN of LE (or the ICA or store on Sped-delivery.)
        ['TOT_CHARGE', 'C', 18, 'R'],     #Total amount invoice charges
        ['TOT_DISCOUNT', 'C', 18, 'R'],   #Total amount invoice discount
        ['DISTRIBUTION', 'C', 3, 'AN'],       #ICA = ICA distributes, LEV = Vendor distributes 
        ['LASTDATECASHDISC', 'C', 12, 'AN'], #Last date for cash discount. Format: CCYYMMDD
        ['DUEDATE', 'C', 12, 'AN'],          #payment due date/Expiration date. Format: CCYYMMDD
        ['TOTALINVOIC', 'C', 18, 'R'],    #Invoice total amount
        ['TOTALLINE_NET', 'C', 18, 'R'],  #Detaljradernas total/Total net line items amount
        ['TOTALTAXABLE', 'C', 18, 'R'],   #Taxable amount
        ['TOTALTAX', 'C', 18, 'R'],       #Total tax amount
        ['SUBJECTPAYDISC', 'C', 18, 'R'], #Total amount subject to payment discount
        ['TAXPERCENTAGE1', 'C', 18, 'R'], #Tax rate as %
        ['TAXAMOUNT1', 'C', 18, 'R'],     #Tax amount for this %
        ['TAXPERCENTAGE2', 'C', 18, 'R'], #Tax rate as %
        ['TAXAMOUNT2', 'C', 18, 'R'],     #Tax amount for this %
        ['TAXPERCENTAGE3', 'C', 18, 'R'], #Tax rate as %
        ['TAXAMOUNT3', 'C', 18, 'R'],     #Tax amount for this %
      ],
'LIN':[
        ['BOTSID','M',3,'A'],
        ['NUMBER', 'C', 6, 'N'],             #line number
        ['EAN', 'C', 14, 'AN'],              #article EAN 
        ['SU_ARTICLECODE', 'C', 17, 'AN'],   #supplier article number
        ['QTY_INVOICED', 'C', 18, 'R'],    #quantity invoiced
        ['LINE_NET', 'C', 18, 'R'],        #Line net amount: (Quantity x price per unit) plus fees minus discounts
        ['LISTPRICE', 'C', 18, 'R'],      #List price, ie no discount / fee included.
        ['TAXPERCENTAGE', 'C', 18, 'R'],  #Tax rate as %
        ['LIN_CHARGE', 'C', 18, 'R'],     #line amount charges
        ['LIN_DISCOUNT', 'C', 18, 'R'],   #line amount discount
      ],
     }
