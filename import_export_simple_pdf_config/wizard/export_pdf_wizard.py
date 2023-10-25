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

    partner_id = fields.Many2one('res.partner', domain=[('is_company', '=', True)], string="Partner")

    def element_to_dict(self, element):
        if len(element) == 0:
            return element.text

        if element[0].tag == 'invoice_import_config':
            return [self.element_to_dict(child) for child in element]

        if element[0].tag == 'line':
            # Handling the case where the element contains multiple 'line' tags
            return [
                (4, int(child.text)) if isinstance(child.text, str) and child.text.isdigit()
                else (0, 0, self.element_to_dict(child))
                for child in element
            ]

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
        dict_content = self.element_to_dict(xml_content)
        if dict_content.get('invoice_import_configs'):
            invoice_import_configs = dict_content.pop('invoice_import_configs')
            for config in invoice_import_configs:
                create_vals = {
                    **config,
                    'partner_id': self.partner_id.id,
                    'name': self.partner_id.name,
                    'display_name': self.partner_id.name,
                    'company_id': self.env.user.company_id.id,
                }
                self.env['account.invoice.import.config'].create(create_vals)
        self.partner_id.write(dict_content)

