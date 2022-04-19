"""
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

def print_element(ele, msg='', verbose=False):
    if len(ele) == 0:
        if verbose:
            print ("No element found to print!")
    elif len(ele) > 1:
        if verbose:
            print ("More then one element found to print!")
    else:
        str = "Elment Tag: " + ele[0].tag
        if ele[0].text is not None:
            str =+ "  | Element Text: " + ele[0].text
        print(msg + str)


def convert_field(  tree,
                    specialFunction,
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
            #print_element(tree.xpath(path + '/' + parent, namespaces=XNS))
            if len(tree.xpath(path + '/' + parent, namespaces=XNS)) == 0:
                create_SubElement(tree.xpath(path, namespaces=XNS)[0], parent.split(':')[1])
        path = path + '/' + parent

#Add the new element
    newElement = create_SubElement(tree.xpath(path, namespaces=XNS)[0], tag, staticText, attributeName,  attributeFixedText)

#Run any special functions on the newly created Element
#    functionList = specialFunction.split(',')

#    for f in functionList:
#        #TODO: This could be made into a more 'proper' 'switch case'
#        if f == 'standard_currency':
#            standard_currency(newElement)


#def standard_currency(element):
#    element.set('currencyID', element.xpath('/Invoice/cbc:DocumentCurrencyCode', namespaces=XNS)[0])


def read_CSV(filename):
    file = open (filename)
    csvreader = csv.reader(file)
    header = []
    header = next(csvreader)
    instructions = []
    for row in csvreader:
        instructions.append(row)
    file.close()

    instructions = adjust_instructions(header, instructions)

    #for n in instructions:
    #    print(n)

    return instructions


def adjust_instructions(header, instructions):

    column = 0
    for h in header:
        
        if header == 'fullParents':
            
            for i in instructions:

                splitParent = i[h].split('/')
                
                if len(splitParent) > 1:
                    newParent = splitParent[0]
                    for p in splitParent[1:]:
                        newParent =+ '/cac:' + p
                    i[h] = newParent
            

    return instructions




def create_invoice ():
    invoice = etree.Element("Invoice", nsmap=NSMAP)

    for n in read_CSV('/usr/share/odoo-edi/edi_peppol_base/data/instruction.toPeppol.csv'):
        convert_field(invoice, n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10])

    return invoice



class ToPeppolInstructions(models.Model):
    _description = "Instructions for converting Odoo objects into PEPPOL. Each row is corresponds to one 'field' in PEPPOL"
    _name = 'instruction.toPeppol'
    _order = 'instruction_id'

#TODO: Add help='' to these fields

    fullParents = fields.Char(string='Full Parents', required=True)
    tag = fields.Char(string='Tag', required=True)
    staticText = fields.Char(string='Static Text')

"""