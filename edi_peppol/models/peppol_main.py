
from peppol_invoice_from_odoo import create_invoice
from peppol_validate import validate_peppol

from lxml import etree


tree = etree.ElementTree(create_invoice())
tree.write('../demo/output.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

validate_peppol('../demo/output.xml')
#validate_peppol('../demo/base-example.xml')