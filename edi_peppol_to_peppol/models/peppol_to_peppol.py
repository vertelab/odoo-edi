import logging, inspect

from lxml import etree

from odoo import models, api, _, fields
from odoorpc import ODOO


_logger = logging.getLogger(__name__)

class XMLNamespaces:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"


NSMAP={'cac':XMLNamespaces.cac, 'cbc':XMLNamespaces.cbc, None:XMLNamespaces.empty}

XNS={   'cac':XMLNamespaces.cac,   
        'cbc':XMLNamespaces.cbc}

ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


class Peppol_To_Peppol(models.Model):
    _name = "peppol.topeppol"
    _inherit = ["peppol.base"]
    _description = "Module for converting from Odoo to PEPPOL"

    def create_SubElement (self, 
                           parent, 
                           tag, 
                           value=None, 
                           attri_name=None, 
                           attri_value=None):
        if value == None:
            nsp = 'cac'
        else:
            nsp = 'cbc'

        result = etree.SubElement(parent, etree.QName(NSMAP[nsp], tag))
        if value is not None:
            result.text = self.convert_to_string(value).strip()

        if attri_name is not None and attri_value is not None:
            if attri_name != '' and attri_value != '':
                result.set(attri_name, attri_value)


        return result

    def getfield(self, lookup, inst=None):

        if lookup is None:
            return None

        if inst is None:
            inst = self

        l = lookup.split(',', 1)
        current_module = l[0].rsplit('.', 1)[0] 
        current_field_name = l[0].rsplit('.', 1)[1]
        try:
            current_field_value = inst[current_field_name]
        except:
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + 
                            "exception found when trying to find: " + 
                            f"{current_field_name=}" + " for inst: " + 
                            str(f"{inst=}"))
            return None

        if len(l) == 1:
            return current_field_value
        else:
            ln = l[1].split(',', 1)
            next_module = ln[0].rsplit('.', 1)[0] 
            inst = inst.env[next_module].browse(current_field_value.id)  
            return self.getfield(l[1], inst)

    def convert_field(  self,
                        tree,
                        fullParent, 
                        tag, 
                        text=None, 
                        datamodule=None, 
                        attri=None,  
                        recordset=None,
                        expects_bool=None,
                        ):

    #Ensures attribute is set
        if attri != None:
            attribute = attri.split(':')
            if len(attribute) == 1:
                attribute = [attribute[0], '']
        else:
            attribute = [None, None]

    #Skips adding a field, if no data for said field can be found:
        if (text is None or text == '') and self.getfield(datamodule, recordset) is None:
            return

    #Ensure that the full Parent path exists
        parents = fullParent.split('/')
        path = '/'
        for parent in parents:
            if parent != "Invoice":
                if len(tree.xpath(path + '/' + parent, namespaces=XNS)) == 0:
                    self.create_SubElement(tree.xpath(path, namespaces=XNS)[0], 
                                           parent.split(':')[1])
            path = path + '/' + parent

    #Fetch data from odoo to element or the static text
        if datamodule is not None:
            value = self.getfield(datamodule, recordset)
            if isinstance(value, bool) and expects_bool is None:
                value = None
        elif text is not None:
            value = text
        else:
            value = None

    #Add the new element
        new_element = None
        if value != None:
            new_element = self.create_SubElement(tree.xpath(path, 
                                                            namespaces=XNS)[0],
                                                            tag, 
                                                            value, 
                                                            attribute[0], 
                                                            attribute[1])

        return new_element

    def remove_empty_elements(self, tree):
        n = 0
        removal_done = True
        while removal_done:
            removal_done = False
            iterator = etree.iterwalk(tree)
            for action, elem in iterator:
                parent = elem.getparent()
                if len(list(elem)) == 0 and elem.text is None:
                    _logger.warning(inspect.currentframe().f_code.co_name + 
                                    ": Removing empty element: " + 
                                    f"{elem.tag}")
                    parent.remove(elem)
                    removal_done = True
            n += 1
            if n > 10000:
                _logger.error(inspect.currentframe().f_code.co_name + 
                              ": More loops then 10000 done. " + 
                              "Exiting function to avoid infinite loop.")
                return None

        return tree

    def convert_party(self, tree, full_parent, datamodulepath):
        full_parent += '/cac:Party'
        self.convert_field(tree, full_parent, 'EndpointID', 
                           datamodule=datamodulepath + '.vat', 
                           attri='schemeID:9955') #TODO: No error check here! Assumed to be swedish VAT number!
        #Not handled: full_parent + /PartyIdentification/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyIdentification/
        #Not handled: full_parent + /PartyName/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyName/cbc-Name/
        self.convert_address(tree, full_parent + '/cac:PostalAddress', datamodulepath)
        self.convert_field(tree, full_parent + '/cac:PartyTaxScheme', 'CompanyID', 
                           datamodule=datamodulepath + '.vat')
        self.convert_field(tree, full_parent + '/cac:PartyTaxScheme/cac:TaxScheme', 'ID', 
                           text='VAT')
        self.convert_field(tree, full_parent + '/cac:PartyLegalEntity', 'RegistrationName', 
                           datamodule=datamodulepath + '.name')
        #Not Handled: full_parent + /PartyLegalEntity/CompanyID: Might be Organisation number. Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyID/
        #Not Handled: full_parent + /PartyLegalEntity/CompanyLegalForm: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyLegalForm/
        #Not Handled: full_parent + /Contact/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-Contact/cbc-Name/
        self.convert_field(tree, full_parent + '/cac:Contact', 'Telephone', 
                           datamodule=datamodulepath + '.phone')
        self.convert_field(tree, full_parent + '/cac:Contact', 'ElectronicMail', 
                           datamodule=datamodulepath + '.email') 

    def convert_address(self, tree, full_parent, datamodulepath):
        #full_parent += '/cac:PostalAddress'
        self.convert_field(tree, full_parent, 'StreetName', 
                           text=self.get_company_street(datamodulepath + '.street')[0])
        self.convert_field(tree, full_parent, 'AdditionalStreetName', 
                           datamodule=datamodulepath + '.street2')
        self.convert_field(tree, full_parent, 'CityName', 
                           datamodule=datamodulepath + '.city')
        self.convert_field(tree, full_parent, 'PostalZone', 
                           datamodule=datamodulepath + '.zip')
        self.convert_field(tree, full_parent, 'CountrySubentity', 
                           datamodule=datamodulepath + '.state_id,res.country.state.name')
        self.convert_field(tree, full_parent + '/cac:AddressLine', 'Line', 
                           text=self.get_company_street(datamodulepath + '.street')[1])
        self.convert_field(tree, full_parent + '/cac:Country', 'IdentificationCode', 
                           datamodule=datamodulepath + '.country_id,res.country.code')

    def get_company_street(self, location):
        original_streets = self.getfield(location)        
        try:    
            streets = original_streets.split(',')
        except:
            return [None, None]
        if len(streets) == 0:
            return [None, None]
        elif len(streets) == 1:
            return [streets[0], None]
        elif len(streets) > 2:
            _logger.Error(inspect.currentframe().f_code.co_name + 
                          ": A unexpected amount of commas where found in '" + 
                          f"{original_streets}" + 
                          "'. Only one or zero commas was expected.")
        
        return streets
