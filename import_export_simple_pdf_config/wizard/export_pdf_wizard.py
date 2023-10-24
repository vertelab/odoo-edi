import base64
from lxml import etree
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ExportConfiguration(models.Model):
    _name = "import.pdf.config.wizard"
    _description = "Export Configuration Wizard"

    simple_pdf_file = fields.Binary(
        string="PDF Config (XML) ", attachment=True
    )
    simple_pdf_filename = fields.Char(string="PDF Config (XML) Filename")

    partner_id = fields.Many2one('res.partner')

    def element_to_dict(self, element):
        if len(element) == 0:
            return element.text

        if element[0].tag == 'line':
            # Handling the case where the element contains multiple 'line' tags
            return [(0, 0, self.element_to_dict(child)) for child in element]

        # Handling other cases where the element contains various tags
        dictionary = {}
        for child in element:
            tag_value = self.element_to_dict(child)
            if isinstance(tag_value, str) and tag_value.isdigit():
                tag_value = int(tag_value)
            dictionary[child.tag] = tag_value
        return dictionary

    def action_export_config(self):
        xml_content = etree.fromstring(base64.b64decode(self.with_context(bin_size=False).simple_pdf_file))
        self.partner_id.write(self.element_to_dict(xml_content))

