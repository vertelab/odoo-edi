import csv

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring
from lxml.isoschematron import Schematron

from odoo import fields, models, api
#TODO: Check if odoo.api and odoo.fields is atually nessesary


class XMLNamespaces:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"


NSMAP={'cac':XMLNamespaces.cac, 'cbc':XMLNamespaces.cbc, None:XMLNamespaces.empty}

XNS={   'cac':XMLNamespaces.cac,   
        'cbc':XMLNamespaces.cbc}

ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


def create_SubElement (parent, tag, text=None, attriName=None, attriValue=None):
    if text == None:
        nsp = 'cac'
    else:
        nsp = 'cbc'

    result = etree.SubElement(parent, QName(NSMAP[nsp], tag))
    result.text = text

    if attriName is not None and attriValue is not None:
        if attriName != '' and attriValue != '':
            result.set(attriName, attriValue)


    return result


def convert_field(  tree,
                    fullParent, 
                    tag, 
                    staticText=None, 
                    datamodule=None, 
                    datamoduleField=None, 
                    attributeName=None, 
                    attributeFixedText=None, 
                    attirbuteDatamodule=None, 
                    attributeDatamoduleField=None):

#Ensure that the full Parent path exists
    parents = fullParent.split('/')

    path = '/'
    for parent in parents:
        if parent != "Invoice":
            if len(tree.xpath(path + '/' + parent, namespaces=XNS)) == 0:
                create_SubElement(tree.xpath(path, namespaces=XNS)[0], parent.split(':')[1])
        path = path + '/' + parent

#Add the new element
    create_SubElement(tree.xpath(path, namespaces=XNS)[0], tag, staticText, attributeName,  attributeFixedText)


def read_CSV(filename):
    file = open (filename)
    csvreader = csv.reader(file)
    header = []
    header = next(csvreader)
    instructions = []
    for row in csvreader:
        instructions.append(row)
    file.close()

    for n in instructions:
        print(n)

    return instructions


def create_invoice ():
    """
    #           Full Parents  , Tag                     , Static Text, [attribute], datamodule, datamodel text field 
    recipe =   [['Invoice'    , 'CustomizationID'       , 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0', '', '', '', '', '', ''], 
                ['Invoice'    , 'ProfileID'             , 'urn:fdc:peppol.eu:2017:poacc:billing:03:1.0', '', '', '', '', '', ''], 
                ['Invoice'    , 'ID'                    , '123456', '', '', '', '', '', ''], 
                ['Invoice'    , 'IssueDate'             , '2020-03-05', '', '', '', '', '', ''], 
                ['Invoice'    , 'DueDate'               , '2020-06-05', '', '', '', '', '', ''], 
                ['Invoice'    , 'DocumentCurrencyCode'  , 'SEK', '', '', '', '', '', ''], 
                ['Invoice'    , 'InvoiceTypeCode'       , '380', '', '', '', '', '', ''], 
                ['Invoice'    , 'BuyerReference'        , 'abs1234', '', '', '', '', '', ''],
                ['Invoice/cac:AccountingSupplierParty/cac:Party'    , 'EndpointID'           , '7300010000001', '', '', 'schemeID', '0088','', ''],
                ['Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country'    , 'IdentificationCode'           , 'SE', '', '', '', '', '', ''],
                ['Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme'    , 'CompanyID'           , 'SE123456789012', '', '', '', '', '', ''],
                ['Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:TaxScheme'    , 'ID'           , 'VAT', '', '', '', '', '', ''],
                ['Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity'    , 'RegistrationName'           , 'Vertel Company LTD', '', '', '', '', '', ''],
                ['Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity'    , 'CompanyID'           , '9876543210', '', '', '', '', '', '']]
"""
    invoice = etree.Element("Invoice", nsmap=NSMAP)

    for n in read_CSV('/usr/share/odoo-edi/edi_peppol/data/instruction.toPeppol.csv'):
        convert_field(invoice, n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9])

    documentcurrencycode = invoice.xpath('/Invoice/cbc:DocumentCurrencyCode', namespaces=XNS)[0]

#AccountingSupplierParty
    #accountingsupplierparty = create_SubElement(invoice, 'AccountingSupplierParty')
    #accountingsupplierpartyParty = create_SubElement(accountingsupplierparty, 'Party')
    #create_SubElement(accountingsupplierpartyParty, 'EndpointID', '7300010000001', schemeID="0088")

    #accountingsupplierpartyPartyPostaladdress = create_SubElement(accountingsupplierpartyParty, 'PostalAddress')
    #accountingsupplierpartyPartyPostaladdressCountry = create_SubElement(accountingsupplierpartyPartyPostaladdress, 'Country')
    #create_SubElement(accountingsupplierpartyPartyPostaladdressCountry, 'IdentificationCode', "SE")

    #accountingsupplierpartyPartyPartytaxscheme = create_SubElement(accountingsupplierpartyParty, 'PartyTaxScheme')
    #create_SubElement(accountingsupplierpartyPartyPartytaxscheme, 'CompanyID', "SE123456789012")

    #accountingsupplierpartyPartyPartytaxschemeTaxscheme = create_SubElement(accountingsupplierpartyPartyPartytaxscheme, 'TaxScheme')
    #create_SubElement(accountingsupplierpartyPartyPartytaxschemeTaxscheme, 'ID', "VAT")


    #accountingsupplierpartyPartyPartylegalentity = create_SubElement(accountingsupplierpartyParty, 'PartyLegalEntity')
    #create_SubElement(accountingsupplierpartyPartyPartylegalentity, 'RegistrationName', "Vertel Company LTD")
    #create_SubElement(accountingsupplierpartyPartyPartylegalentity, 'CompanyID', "9876543210")


#AccountingCustomerParty
    accountingcustomerparty = create_SubElement(invoice, 'AccountingCustomerParty')
    accountingcustomerpartyParty = create_SubElement(accountingcustomerparty, 'Party')
    create_SubElement(accountingcustomerpartyParty, 'EndpointID', '7300010000018', 'schemeID', '0088')

    accountingcustomerpartyPartyPostaladdress = create_SubElement(accountingcustomerpartyParty, 'PostalAddress')
    accountingcustomerpartyPartyPostaladdressCountry = create_SubElement(accountingcustomerpartyPartyPostaladdress, 'Country')
    create_SubElement(accountingcustomerpartyPartyPostaladdressCountry, 'IdentificationCode', "SE")

    accountingcustomerpartyPartyPartylegalentity = create_SubElement(accountingcustomerpartyParty, 'PartyLegalEntity')
    create_SubElement(accountingcustomerpartyPartyPartylegalentity, 'RegistrationName', "Generic Company LTD")


    #TaxTotal
    taxtotal = create_SubElement(invoice, 'TaxTotal')
    create_SubElement(taxtotal, 'TaxAmount', '12.5', 'currencyID', documentcurrencycode.text)

    taxtotalTaxsubtotal = create_SubElement(taxtotal, 'TaxSubtotal')
    create_SubElement(taxtotalTaxsubtotal, 'TaxableAmount', '50', 'currencyID', documentcurrencycode.text)
    create_SubElement(taxtotalTaxsubtotal, 'TaxAmount', '12.5', 'currencyID', documentcurrencycode.text)

    taxtotalTaxsubtotalTaxcategory = create_SubElement(taxtotalTaxsubtotal, 'TaxCategory')
    create_SubElement(taxtotalTaxsubtotalTaxcategory, 'ID', 'S')
    create_SubElement(taxtotalTaxsubtotalTaxcategory, 'Percent', '25')


    taxtotalTaxsubtotalTaxcategoryTaxscheme = create_SubElement(taxtotalTaxsubtotalTaxcategory, 'TaxScheme')
    create_SubElement(taxtotalTaxsubtotalTaxcategoryTaxscheme, 'ID', 'VAT')

  #LegalMonetaryTotal
    legalmonetarytotal = create_SubElement(invoice, 'LegalMonetaryTotal')
    create_SubElement(legalmonetarytotal, 'LineExtensionAmount', '50', 'currencyID', documentcurrencycode.text)
    create_SubElement(legalmonetarytotal, 'TaxExclusiveAmount', '50', 'currencyID', documentcurrencycode.text)
    create_SubElement(legalmonetarytotal, 'TaxInclusiveAmount', '62.5', 'currencyID', documentcurrencycode.text)
    create_SubElement(legalmonetarytotal, 'PayableAmount', '62.5', 'currencyID', documentcurrencycode.text)


    #InivoiceLine
    invoiceline = create_SubElement(invoice, 'InvoiceLine')
    create_SubElement(invoiceline, 'ID', '1')

    #create_SubElement(invoice, 'InvoiceLine')
    #create_SubElement(invoice.xpath('//InvoiceLine')[0], 'ID', '1')

    create_SubElement(invoiceline, 'InvoicedQuantity', '10', 'unitCode', 'XZB')
    create_SubElement(invoiceline, 'LineExtensionAmount', '50', 'currencyID', documentcurrencycode.text)

    invoicelineItem = create_SubElement(invoiceline, 'Item')
    create_SubElement(invoicelineItem, 'Name', 'Jellybeans')

    invoicelineItemClassifiedTaxCategory = create_SubElement(invoicelineItem, 'ClassifiedTaxCategory')
    create_SubElement(invoicelineItemClassifiedTaxCategory, 'ID', 'S')
    create_SubElement(invoicelineItemClassifiedTaxCategory, 'Percent', '25')

    invoicelineItemClassifiedTaxCategoryTaxscheme = create_SubElement(invoicelineItemClassifiedTaxCategory, 'TaxScheme')
    create_SubElement(invoicelineItemClassifiedTaxCategoryTaxscheme, 'ID', 'VAT')

    invoicelinePrice = create_SubElement(invoiceline, 'Price')
    create_SubElement(invoicelinePrice, 'PriceAmount', '5', 'currencyID', documentcurrencycode.text)

    return invoice


""""
class ToPeppolInstructions(models.Model):
    _description = "Instructions for converting Odoo objects into PEPPOL. Each row is corresponds to one 'field' in PEPPOL"
    _name = 'instruction.toPeppol'
    _order = 'instruction_id'

#TODO: Add help='' to these fields

    fullParents = fields.Char(string='Full Parents', required=True)
    tag = fields.Char(string='Tag', required=True)
    staticText = fields.Char(string='Static Text')

"""
