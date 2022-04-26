#from datetime import date, datetime
import datetime
import os, logging, csv, inspect
#from tkinter import E
from jmespath import search

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring
from lxml.isoschematron import Schematron
from odoo import models, api, _, fields
from odoorpc import ODOO




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


class Peppol_To_Peppol(models.Model):
    _name = "peppol.topeppol"
    _inherit = ["peppol.base"]
    _description = "Module for converting from Odoo to PEPPOL"

    def create_SubElement (self, parent, tag, value=None, attri_name=None, attri_value=None):
        if value == None:
            nsp = 'cac'
        else:
            nsp = 'cbc'

        result = etree.SubElement(parent, QName(NSMAP[nsp], tag))
        if value is not None:
            result.text = self.convert_to_string(value).strip()

        if attri_name is not None and attri_value is not None:
            if attri_name != '' and attri_value != '':
                result.set(attri_name, attri_value)


        return result

    def getfield(self, lookup, inst=None):
        #_logger.warning(inspect.currentframe().f_code.co_name + ": " + "Trying to parse: " + lookup)

        if lookup is None:
            return None

        if inst is None:
            inst = self

        l = lookup.split(',', 1)
        current_module = l[0].rsplit('.', 1)[0] 
        current_field_name = l[0].rsplit('.', 1)[1]
        try:
            current_field_value = inst[current_field_name]
            #_logger.error(inspect.currentframe().f_code.co_name + ": " + f"{current_field_value=}" + " is of type " + str(f"{type(current_field_value)=}") + " and came from: " + f"{current_field_name=}")
        except:
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + "exception found when trying to find: " + f"{current_field_name=}" + " for inst: " + str(f"{inst=}"))
            return None

        """
        if lookup == "account.move.partner_id,res.partner.comment" or lookup == "res.partner.comment":
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{current_module=}")
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{current_field_name=}")
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{current_field_value=}")
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{len(l)=}")
        """

        if len(l) == 1:
            return current_field_value
        else:
            ln = l[1].split(',', 1)
            next_module = ln[0].rsplit('.', 1)[0] 
            #_logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{next_module=}")
            inst = inst.env[next_module].browse(current_field_value.id)
            #_logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{inst=}")    
            return self.getfield(l[1], inst)

    def convert_field(  self,
                        tree,
                        #special_function,
                        fullParent, 
                        tag, 
                        text=None, 
                        datamodule=None, 
                        #datamodule_field=None, 
                        attri=None, 
                        #attri_text=None, 
                        attirbute_datamodule=None, 
                        attribute_datamodule_field=None,
                        recordset=None,
                        expects_bool=None,
                        ):

    #Ensures attribute is set
        if attri != None:
            attribute = attri.split(':')
            if len(attribute) == 1:
                attribute = [attribute[0], '']
            #_logger.warning(inspect.currentframe().f_code.co_name + ": " + f"{attribute=}")
        else:
            attribute = [None, None]

    #Skips adding a field, if no data for said field can be found:
        if (text is None or text == '') and self.getfield(datamodule, recordset) is None:
            _logger.warning(inspect.currentframe().f_code.co_name + ": " + "No data found for: " + fullParent + '/' + tag)
            return

    #Ensure that the full Parent path exists
        parents = fullParent.split('/')

        path = '/'
        for parent in parents:
            if parent != "Invoice":
                #print_element(tree.xpath(path + '/' + parent, namespaces=XNS))
                if len(tree.xpath(path + '/' + parent, namespaces=XNS)) == 0:
                    self.create_SubElement(tree.xpath(path, namespaces=XNS)[0], parent.split(':')[1])
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
            new_element = self.create_SubElement(tree.xpath(path, namespaces=XNS)[0], tag, value, attribute[0], attribute[1])
        #new_element.text = self.convert_to_string(value)

        return new_element

    """
    def adjust_instructions(self, header, instructions):

        column = 0
        for h in header:
            
            if header == 'fullParents':
                pass

        return instructions
    """

    def remove_empty_elements(self, tree):
        n = 0
        removal_done = True
        while removal_done:
            removal_done = False
            iterator = etree.iterwalk(tree)
            for action, elem in iterator:
                parent = elem.getparent()
                if len(list(elem)) == 0 and elem.text is None:
                #if elem is None and elem.text is None:
                    _logger.warning(inspect.currentframe().f_code.co_name + ": Removing element: " + f"{elem.tag}")
                    parent.remove(elem)
                    removal_done = True
            n += 1
            #_logger.warning(inspect.currentframe().f_code.co_name + ": removal loops done: " + f"{n}")
            if n > 10000:
                _logger.error(inspect.currentframe().f_code.co_name + ": More loops then 10000 done. Exiting function to avoid infinite loop")
                return None

        return tree