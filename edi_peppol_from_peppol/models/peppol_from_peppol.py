import logging, inspect

from lxml import etree

from odoo import models, api, _, fields
from odoorpc import ODOO
from xmlschema import XMLSchema10


_logger = logging.getLogger(__name__)

# Class containing functions that all From-PEPPOL-To-Odoo classes may need to use.
class Peppol_From_Peppol(models.Model):
    _name = "peppol.frompeppol"
    _inherit = ["peppol.base"]
    _description = "Module for converting from PEPPOL to Odoo"

    def parse_xml(self, msg):
        try:
            tree = etree.parse(msg)
        except Exception as e:
            _logger.error(inspect.currentframe().f_code.co_name + ": " +
            "Tried to import a xml file, but failed to, due to: " + f"{e}")
            return None
        else:
            return tree

    def get_xml(self, tree, xmlpath, iteration=0):
        try:
            value = tree.xpath(xmlpath, namespaces=self.nsmapf().XNS)[iteration]
        except Exception as e:
            _logger.warning(inspect.currentframe().f_code.co_name + ": " +
            "Tried to import the xml value for: " + f"{xmlpath}" + "\n" +
            ", but it failed due to: " + f"{e}")
            #_logger.error(e)
            return None
        else:
            return value

    def get_xml_value(self, tree, xmlpath, iteration=0):
        try:
            value = self.get_xml(tree, xmlpath, iteration).text
        except:
            return None
        try:
            value = value.strip()
        except:
            pass
        return value

    # TODO: This should not be static 'SEK', but rather take its value from the XML!
    def get_currency_by_name(self):
        return self.env['res.currency'].search([('name', '=', 'SEK')]).id

    # Compares the information of a company in the xml-tree 'tree'
    #  with the xml parent 'xmlpath' which should be pointing out a cac:Party
    #  and the company 'db_company' which is in the database.
    # The information from these two sources should be the same.
    # If it is the same, it will return 'None'.
    # If there is a missmatch it will return a list,
    #  consisting of two elements, where each element is a list of two elements.
    # [0][#] will contain info about the data from the database.
    # [1][#] will contain info about the data from the xml.
    # [#][0] will contain what type of value was actualy wrong.
    # [#][1] will contain the actual value itself.
    def is_company_info_correct(self, tree, db_company, xmlpath):

        # Check Company Name
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PartyLegalEntity/cbc:RegistrationName'),
            db_company.name,
            'Company Name')
        if t is not None:
            return t

        # Check CompanyID
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PartyTaxScheme/cbc:CompanyID'),
            db_company.vat,
            'Company ID')
        if t is not None:
            return t

        # Checks Vat-Account
        t =  self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cbc:EndpointID'),
            db_company.vat,
            'Vat-Account')
        if t is not None:
            return t

        # Checks Street address
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PostalAddress/cbc:StreetName'),
            self.get_company_street(db_company.street)[0],
            'Street')
        if t is not None:
            return t

        # Check Street address sub-divison (such as 'appartment 12')
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PostalAddress/cac:AddressLine/cbc:Line'),
            self.get_company_street(db_company.street)[1],
            'Street Sub-Division')
        if t is not None:
            return t

        # Checks City
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PostalAddress/cbc:CityName'),
            db_company.city,
            'City')
        if t is not None:
            return t

        # Checks Zip-Codes
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PostalAddress/cbc:PostalZone'),
            db_company.zip,
            'Zip-Code')
        if t is not None:
            return t

        # Check CountrySubentity
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PostalAddress/cbc:CountrySubentity'),
            db_company.state_id.name,
            'State')
        if t is not None:
            return t

        # Check Country
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:PostalAddress/cac:Country/cbc:IdentificationCode'),
            db_company.country_id.code,
            'Country')
        if t is not None:
            return t

        # Check Telephone
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:Contact/cbc:Telephone'),
            db_company.phone,
            'Telephone')
        if t is not None:
            return t

        # Check E-Mail
        t = self.company_comparison(
            self.get_xml_value(tree, xmlpath + '/cac:Contact/cbc:ElectronicMail'),
            db_company.email,
            'E-Mail')
        if t is not None:
            return t

        return None

    def company_comparison(self, xml, db, name):
        if (xml is None and db is None) or (xml is None and db is False):
            return None
        if xml is None or db is None:
            _logger.error(inspect.currentframe().f_code.co_name +
                " found the following two to not match: " + f"{db}" +
                " and " + f"{xml}")
            return [['Database ' + name, '\'' + f"{db}" + '\''],
                    ['Invoice     ' + name, '\'' + f"{xml}" + '\'']]

        db = ''.join(f'{db}'.split())
        db = db.lower().replace('-', '')
        xml = ''.join(f'{xml}'.split())
        xml = xml.lower().replace('-', '')

        if db != xml:
            _logger.error(inspect.currentframe().f_code.co_name +
                          " found the following two to not match: " + f"{db}" +
                          " and " + f"{xml}")
            return [['Database ' + name, '\'' + f"{db}" + '\''],
                    ['Invoice     ' + name, '\'' + f"{xml}" + '\'']]
        return None

    # Compares the product infomation of a converted-to-odoo line, and what it says in the xml
    def is_product_info_correct(self, line, xml):
        if str(line.product_id.name) != str(self.xpft(xml, './cac:Item/cbc:Name')):
            return False, [['In Odoo:    Product Name', line.product_id.name],
                           ['In Invoice: Product Name',self.xpft(xml, './cac:Item/cbc:Name')]]

        if str(line.price_unit) != str(self.xpft(xml, './cac:Price/cbc:PriceAmount')):
            return False, [['In Odoo:    Unit Price', line.price_unit],
                           ['In Invoice: Unit Price',self.xpft(xml, './cac:Price/cbc:PriceAmount')]]

        if str(line.quantity) != str(self.xpft(xml, './cbc:InvoicedQuantity')):
            return False, [['In Odoo:    Quantity', line.quantity],
                           ['In Invoice: Quantity',self.xpft(xml, './cbc:InvoicedQuantity')]]

        if str(line.price_subtotal) != str(self.xpft(xml, './cbc:LineExtensionAmount')):
            return False, [['In Odoo:    Subtotal', line.price_subtotal],
                           ['In Invoice: Subtotal',self.xpft(xml, './cbc:LineExtensionAmount')]]

        xml_tax_id = self.env['account.tax'].search([('name', '=',
                        self.translate_tax_category_from_peppol(
                            self.xpft(xml, './cac:Item/cac:ClassifiedTaxCategory/cbc:ID'),
                            self.xpft(xml, './cac:Item/cac:ClassifiedTaxCategory/cbc:Percent')))])
        if line.tax_ids.id != xml_tax_id.id:
            return False, [['In Odoo:    Tax-Group', line.tax_ids.name],
                           ['In Invoice: Tax-Group', xml_tax_id.name]]

        return True, None

    def find_company_id(self, tree, xmlpath):
        endpointID = self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')
        return self.env['res.partner'].search([('vat', '=', endpointID),
                                               ('is_company', '=', 't')]).id

    """
    def get_vat_id(self, peppol_rate):
        odoo_vat_name = self.translate_tax_category_from_peppol(peppol_rate)
        if odoo_vat_name:
            try:
                return self.env['account.tax'].search([('name', '=', odoo_vat_name)])[0]
            except:
                _logger.error(inspect.currentframe().f_code.co_name +
                              ": Was unable to find the tax group named: " +
                              f"{odoo_vat_name=}" + " despite it being expected.")
        return None
    """

    # Translates the base swedish vat-taxes, from PEPPOL format into Odoo.
    # TODO: add more detailed translation, which leads to other vat-codes then just I's
    def translate_tax_category_from_peppol(self, tax_type, tax_percent):
        tax_category_dict_S = {
            '25.0' : 'I',
            '12.0' : 'I12',
            '6.0' : 'I6',
        }
        if input is None:
            return None

        output = None
        try:
            if tax_type == 'S':
                output = tax_category_dict_S[tax_percent]
            else:
                raise
        except:
            _logger.error(inspect.currentframe().f_code.co_name +
                          ": Tax code of " +
                          str(f"{input=}") +
                          " could not be translated into Odoo format!")
        return output