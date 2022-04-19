import os, logging, csv

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring
from lxml.isoschematron import Schematron
from odoo import models, api, _, fields

#from peppol_invoice_from_odoo import create_invoice
#from edi_peppol_validate import validate_peppol

#from lxml import etree, html

_logger = logging.getLogger(__name__)

class XMLNamespaces:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

NSMAP={'cac':XMLNamespaces.cac, 'cbc':XMLNamespaces.cbc, None:XMLNamespaces.empty}

XNS={   'cac':XMLNamespaces.cac,   
        'cbc':XMLNamespaces.cbc}

ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


class Peppol(models.Model):
    _name = "peppol.peppol"

    def test(self):
        _logger.warning("Hej!")


    def create_SubElement (self, parent, tag, text=None, attri_name=None, attri_value=None):
        if text == None:
            nsp = 'cac'
        else:
            nsp = 'cbc'

        result = etree.SubElement(parent, QName(NSMAP[nsp], tag))
        result.text = text

        if attri_name is not None and attri_value is not None:
            if attri_name != '' and attri_value != '':
                result.set(attri_name, attri_value)


        return result


    def print_element(self, ele, msg='', verbose=False):
        if len(ele) == 0:
            if verbose:
                _logger.warning("No element found to print!")
        elif len(ele) > 1:
            if verbose:
                _logger.warning("More then one element found to print!")
        else:
            str = "Elment Tag: " + ele[0].tag
            if ele[0].text is not None:
                str =+ "  | Element Text: " + ele[0].text
            print(msg + str)


    def convert_field(  self,
                        tree,
                        special_function,
                        fullParent, 
                        tag, 
                        static_text=None, 
                        datamodule=None, 
                        datamodule_field=None, 
                        attribute_name=None, 
                        attributeFixedText=None, 
                        attirbute_datamodule=None, 
                        attribute_datamodule_field=None):

    #Ensure that the full Parent path exists
        parents = fullParent.split('/')

        path = '/'
        for parent in parents:
            if parent != "Invoice":
                #print_element(tree.xpath(path + '/' + parent, namespaces=XNS))
                if len(tree.xpath(path + '/' + parent, namespaces=XNS)) == 0:
                    self.create_SubElement(tree.xpath(path, namespaces=XNS)[0], parent.split(':')[1])
            path = path + '/' + parent

    #Add the new element
        new_element = self.create_SubElement(tree.xpath(path, namespaces=XNS)[0], tag, static_text, attribute_name,  attributeFixedText)

    #Run any special functions on the newly created Element
    #    functionList = special_function.split(',')

    #    for f in functionList:
    #        #TODO: This could be made into a more 'proper' 'switch case'
    #        if f == 'standard_currency':
    #            standard_currency(new_element)


    def adjust_instructions(self, header, instructions):

        column = 0
        for h in header:
            
            if header == 'fullParents':
                pass

        return instructions


    def read_CSV(self, filename):
        file = open (filename)
        csvreader = csv.reader(file)
        header = []
        header = next(csvreader)
        instructions = []
        for row in csvreader:
            instructions.append(row)
        file.close()

        instructions = self.adjust_instructions(header, instructions)

        #for n in instructions:
        #    print(n)

        return instructions


    def create_invoice(self):
        invoice = etree.Element("Invoice", nsmap=NSMAP)

        for n in self.read_CSV('/usr/share/odoo-edi/edi_peppol_base/data/instruction.toPeppol.csv'):
            self.convert_field(invoice, n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[8], n[9], n[10])

        return invoice


    def invoice_to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())
        _logger.warning("XML has ID: " + tree.xpath('/Invoice/cbc:ID/text()', namespaces=XNS)[0])
        tree.write('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

        

        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml')
        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol_base/demo/base-example.xml')


#if __name__ == "__main__":
#    main()    