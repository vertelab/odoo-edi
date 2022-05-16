import logging, inspect

from lxml import etree

from odoo import models, api, _, fields
from odoorpc import ODOO


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
            _logger.error(inspect.currentframe().f_code.co_name + ": " +
            "Tried to import a xml value, but it failed due to: " + f"{e}")
            #_logger.error(e)
            return None
        else:
            return value

    def get_xml_value(self, tree, xmlpath, iteration=0):
        try:
            value = self.get_xml(tree, xmlpath, iteration).text
        except:
            return None
        return value

    def get_currency_by_name(self):
        return self.env['res.currency'].search([('name', '=', 'SEK')]).id

    # TODO: This should check more then just vat numbers.
    # Things like: street address, phone number, and similar.
    def is_company_info_correct(self, tree, datamodule, xmlpath):
        #dm = datamodule.rsplit('.', 1)
        #db_company = self[dm[1]]
        db_company = datamodule

        #_logger.warning(inspect.currentframe().f_code.co_name + " : " +
        #                f"{datamodule=}" + "   " +
        #                f"{db_company.vat=}")
        if db_company.vat != self.get_xml_value(tree, xmlpath + '/cbc:EndpointID'):
            _logger.error(inspect.currentframe().f_code.co_name +
                          " found the following two to not match: " + f"{db_company.vat=}" +
                          " and " + f"{self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')=}")
            return False, [['Own Vat-Account', db_company.vat],
                           ['Invoice Vat-Account',
                            self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')]]

        #TODO: Add checks of more types of info, like: street, phone number, name, and such.
        return True, None

    # Compares the product infomation of a converted-to-odoo line, and what it says in the xml
    def is_product_info_correct(self, line, xml):
        if str(line.price_unit) != str(self.xpft(xml, './cac:Price/cbc:PriceAmount')):
            return False, [['In Odoo: Unit Price', line.price_unit],
                           ['In Invoice: Unit Price',self.xpft(xml, './cac:Price/cbc:PriceAmount')]]

        if str(line.quantity) != str(self.xpft(xml, './cbc:InvoicedQuantity')):
            return False, [['In Odoo: Quantity', line.quantity],
                           ['In Invoice: Quantity',self.xpft(xml, './cbc:InvoicedQuantity')]]

        if str(line.price_subtotal) != str(self.xpft(xml, './cbc:LineExtensionAmount')):
            return False, [['In Odoo: Subtotal', line.price_subtotal],
                           ['In Invoice: Subtotal',self.xpft(xml, './cbc:LineExtensionAmount')]]

        xml_tax_id = self.env['account.tax'].search([('name', '=',
                        self.translate_tax_category_from_peppol(
                            self.xpft(xml, './cac:Item/cac:ClassifiedTaxCategory/cbc:Percent')))])
        if line.tax_ids.id != xml_tax_id.id:
            return False, [['In Odoo: Tax-Group', line.tax_ids.name],
                           ['In Invoice: Quantity', xml_tax_id.name]]

        return True, None

    def find_company_id(self, tree, xmlpath):
        endpointID = self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')
        return self.env['res.partner'].search([('vat', '=', endpointID),
                                               ('is_company', '=', 't')]).id

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