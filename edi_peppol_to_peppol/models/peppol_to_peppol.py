import logging, inspect

from lxml import etree

from odoo import models, api, _, fields
from odoorpc import ODOO

_logger = logging.getLogger(__name__)


# Class containing functions that all From-Odoo-To-PEPPOL classes may need to use.
class Peppol_To_Peppol(models.Model):
    _name = "peppol.topeppol"
    _inherit = ["peppol.base"]
    _description = "Module for converting from Odoo to PEPPOL"

    # Created a new lxml SubElement and returns it
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

        result = etree.SubElement(parent, etree.QName(self.nsmapt().NSMAP[nsp], tag))
        if value is not None:
            result.text = self.convert_to_string(value).strip()
        if attri_name is not None and attri_value is not None:
            if attri_name != '' and attri_value != '':
                result.set(attri_name, attri_value)
        return result

    # Converts to the field 'fullParent' + 'tag' in the xml-file which is in PEPPOL format,
    #  with the data in it comming either from 'text',
    #  or from a spesific modules tablefrom Odoo as defined in 'datamodule'.
    # 'attri' is for attributes that must be set in PEPPOL.
    # 'recordset' defines a different module to start from,
    #  when trying to fetch the datamodule, then 'self'
    def convert_field(  self,
                        tree,
                        fullParent,
                        tag,
                        text=None,
                        attri=None,
                        expects_bool=None,
                        ):

    # Ensures attribute is set
        if attri != None:
            attribute = attri.split(':')
            if len(attribute) == 1:
                attribute = [attribute[0], '']
        else:
            attribute = [None, None]

    # Skips adding a field, if no text is inputet for this field:
        if (text is None or text == ''):
            return

    # Ensure that the full Parent path exists
        parents = fullParent.split('/')
        path = '/'
        for parent in parents:
            if parent != "Invoice":
                if len(tree.xpath(path + '/' + parent, namespaces=self.nsmapt().XNS)) == 0:
                    self.create_SubElement(tree.xpath(path, namespaces=self.nsmapt().XNS)[0],
                                           parent.split(':')[1])
            path = path + '/' + parent

    # Returns the newly created element
        return self.create_SubElement(tree.xpath(path,
                                      namespaces=self.nsmapt().XNS)[0],
                                      tag,
                                      text,
                                      attribute[0],
                                      attribute[1])

    # Iterates through the entire given 'tree', and removes any elements that neither has:
    #  any children nor has a text in them.
    # This is done repeatedly, so that in the end only element that either has some text,
    # or has a child (or grand-child of any order) that has some text, remain in the tree.
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
            # Infinite-loop prevention.
            if n > 10000:
                _logger.error(inspect.currentframe().f_code.co_name +
                              ": More loops then 10000 done. " +
                              "Exiting function to avoid infinite loop.")
                return None
        return tree

    # Converts a 'cac:Party' from Odoo to PEPPOL
    def convert_party(self, tree, full_parent, dm):
        full_parent += '/cac:Party'
        self.convert_field(tree, full_parent, 'EndpointID',
                           text=dm.vat,
                           attri='schemeID:9955') #TODO: No error check here! Assumed to be swedish VAT number!
        #Not handled: full_parent + /PartyIdentification/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyIdentification/
        #Not handled: full_parent + /PartyName/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyName/cbc-Name/
        self.convert_address(tree, full_parent + '/cac:PostalAddress', dm)
        self.convert_field(tree, full_parent + '/cac:PartyTaxScheme', 'CompanyID',
                           text=dm.vat)
        self.convert_field(tree, full_parent + '/cac:PartyTaxScheme/cac:TaxScheme', 'ID',
                           text='VAT')
        self.convert_field(tree, full_parent + '/cac:PartyLegalEntity', 'RegistrationName',
                           text=dm.name)
        #Not Handled: full_parent + /PartyLegalEntity/CompanyID: Might be Organisation number. Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyID/
        #Not Handled: full_parent + /PartyLegalEntity/CompanyLegalForm: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyLegalForm/
        #Not Handled: full_parent + /Contact/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-Contact/cbc-Name/
        self.convert_field(tree, full_parent + '/cac:Contact', 'Telephone',
                           text=dm.phone)
        self.convert_field(tree, full_parent + '/cac:Contact', 'ElectronicMail',
                           text=dm.email)

    # Converts a 'cac:PostalAddress' or a 'cac:Address' from Odoo to PEPPOL
    def convert_address(self, tree, full_parent, dm):
        #full_parent += '/cac:PostalAddress'
        _logger.warning(dm)
        self.convert_field(tree, full_parent, 'StreetName',
                           text=self.get_company_street(dm.street)[0])
        self.convert_field(tree, full_parent, 'AdditionalStreetName',
                           text=dm.street2)
        self.convert_field(tree, full_parent, 'CityName',
                           text=dm.city)
        self.convert_field(tree, full_parent, 'PostalZone',
                           text=dm.zip)
        self.convert_field(tree, full_parent, 'CountrySubentity',
                           text=dm.state_id.name)
        self.convert_field(tree, full_parent + '/cac:AddressLine', 'Line',
                           text=self.get_company_street(dm.street)[1])
        self.convert_field(tree, full_parent + '/cac:Country', 'IdentificationCode',
                           text=dm.country_id.code)

