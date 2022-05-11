import logging, inspect

from lxml import etree

from odoo import models, api, _, fields
from odoorpc import ODOO


_logger = logging.getLogger(__name__)


class NSMAPS:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, 'ubl':empty}

    XNS={'cac':cac,   
         'cbc':cbc,
         'ubl':empty}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


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

    def append_odoo_data(self, tree, destination, xmlpath=None, text=None):
        _logger.error(inspect.currentframe().f_code.co_name + ": " +
                      "THIS FUNCTION IS NOT CORRECTLY IMPLEMENTED YET!")
        self.set_odoo_data(tree, destination, xmlpath, text, True)



    def set_odoo_data(self, tree, destination, xmlpath=None, text=None, append=False):
        if xmlpath is not None:
            value = self.get_xml_value(tree, xmlpath)
        else:
            value = text

        if value is None:
            _logger.error(inspect.currentframe().f_code.co_name + ": " +
            "Returned None!")
            return None

        try:
            self.set_odoo_value(destination, value)
        except Exception as e:
            _logger.error(inspect.currentframe().f_code.co_name + ": " + 
            "With " + f"{append=}" + " tried to export " + f"{value=}" + " to odoo, but failed due to:")
            _logger.exception(e)
            #_logger.error(e)

    def get_xml(self, tree, xmlpath, iteration=0):
        #_logger.warning(inspect.currentframe().f_code.co_name + ": " +
        #f"{xmlpath=}")
        try:
            value = tree.xpath(xmlpath, namespaces=NSMAPS.XNS)[iteration]
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
        
    """
            if len(value) == 0:
                _logger.error(inspect.currentframe().f_code.co_name + ": " +
                "Returned None!")
                return None
            else:
                try:
                    _logger.error(f"{value=}")
                    return value
                except:
                    _logger.error(inspect.currentframe().f_code.co_name + ": " + 
                    "Tried to import a xml value, but it failed to, due to: ")  
                    _logger.error(e)                 
        return None
    """

    

    def set_odoo_value(self, destination, value, inst=None, append=False):
        if destination is None or value is None:
            _logger.error(inspect.currentframe().f_code.co_name + ": " +
            "Returned None!")
            return None

        if inst is None:
            inst = self        

        d = destination.split(',', 1)
        current_module = d[0].rsplit('.', 1)[0] 
        current_field_name = d[0].rsplit('.', 1)[1]

        if len(d) == 1:
            if append:
                old_value = self.getfield(destination)
                if old_value is not None and old_value != '':
                    value = self.convert_to_string(old_value) + ',' + self.convert_to_string(value)
            try:
                inst[current_field_name] = value
            except:
                return None
            return True
        else:
            return None #TODO: This should work recursively.

    def get_currency_by_name(self):
        return self.env['res.currency'].search([('name', '=', 'SEK')]).id
        
    # TODO: This should check more then just vat numbers, but also things like street address, phone number, and similar.    
    def is_company_info_correct(self, tree, datamodule, xmlpath):
        dm = datamodule.rsplit('.', 1)
        db_company = self[dm[1]]
        
        if db_company.vat != self.get_xml_value(tree, xmlpath + '/cbc:EndpointID'):
            _logger.error(inspect.currentframe().f_code.co_name + 
                          " found the following two to not match: " + f"{db_company.vat=}" + 
                          " and " + f"{self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')=}")
            return False, [['Own Vat-Account', db_company.vat], ['Invoice Vat-Account', self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')]]

        #TODO: Add checks of more types of info, like: street, phone number, name, and such.
        return True, None

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
                        self.translate_tax_category_to_peppol(
                            self.xpft(xml, './cac:Item/cac:ClassifiedTaxCategory/cbc:Percent')))])
        if line.tax_ids.id != xml_tax_id.id:
            return False, [['In Odoo: Tax-Group', line.tax_ids.name],
                           ['In Invoice: Quantity', xml_tax_id.name]]           

        return True, None

    #def is_invoice_info_correct(self, tree):



    def find_company_id(self, tree, xmlpath):
        endpointID = self.get_xml_value(tree, xmlpath + '/cbc:EndpointID')

        #_logger.error(inspect.currentframe().f_code.co_name + ": " + f"{self.env['res.partner'].search([('vat', '=', endpointID),('is_company', '=', 't')]).id=}")
        return self.env['res.partner'].search([('vat', '=', endpointID),('is_company', '=', 't')]).id

    def get_vat_id(self, peppol_rate):
        odoo_vat_name = self.translate_tax_category_to_peppol(peppol_rate)
        if odoo_vat_name:
            #_logger.error(inspect.currentframe().f_code.co_name + ": " + f"{self.env['account.tax'].search([('name', '=', odoo_vat_name)])=}")
            try:
                return self.env['account.tax'].search([('name', '=', odoo_vat_name)])[0]
            except:
                _logger.error(inspect.currentframe().f_code.co_name + ": Was unable to find the tax group named: " + f"{odoo_vat_name=}" + " despite it being expected.")
        return None