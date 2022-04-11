import os

from lxml import etree

from peppol_invoice_from_odoo import create_invoice
from peppol_validate import validate_peppol


tree = etree.ElementTree(create_invoice())
tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

validate_peppol('/usr/share/odoo-edi/edi_peppol/demo/output.xml')
validate_peppol('/usr/share/odoo-edi/edi_peppol/demo/base-example.xml')