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

    # partner_id = fields.Many2one('res.partner', domain=[('is_company', '=', True)], string="Partner")

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

    def _partner_rec(self, name, email=False):
        if email:
            partner_id = self.env['res.partner'].search([('email', '=', email)], limit=1)
        else:
            partner_id = self.env['res.partner'].search([('name', '=', name)], limit=1)

        if not partner_id:
            partner_id = self.env['res.partner'].create({
                'name': name,
                'email': email,
                'company_type': 'company'
            })
        return partner_id

    def _account_rec(self, code):
        account_id = self.env['account.account'].search([('code', '=', code)], limit=1)
        if not account_id:
            raise ValidationError(f"Account with {code} does not exist")
        return account_id

    def _tax_rec(self, tax_name):
        account_id = self.env['account.tax'].search([('name', '=', tax_name)], limit=1)
        if not account_id:
            raise ValidationError(f"Account with {tax_name} does not exist")
        return account_id

    def action_export_config(self):
        xml_content = etree.fromstring(base64.b64decode(self.with_context(bin_size=False).simple_pdf_file))
        dict_content = self.element_to_dict(xml_content)

        partner_id = self._partner_rec(dict_content.pop('name'), dict_content.pop('email', False))

        print(dict_content)

        if dict_content.get('invoice_import_configs'):
            invoice_import_configs = dict_content.pop('invoice_import_configs')
            for config in invoice_import_configs:
                tax_ids = [(4, self._tax_rec(tx[-1]).id) for tx in config.pop('tax_ids')]
                create_vals = {
                    **config,
                    'partner_id': partner_id.id,
                    'name': partner_id.name,
                    'display_name': partner_id.name,
                    'account_id': self._account_rec(config.get('account_id')).id,
                    'tax_ids': tax_ids
                    # 'company_id': self.env.user.company_id.id,
                }
                print(create_vals)
                self.env['account.invoice.import.config'].create(create_vals)

        # print(miracle)
        if dict_content.get('simple_pdf_field_ids'):
            for _field in dict_content.get('simple_pdf_field_ids'):
                _field[-1].update({'partner_id': partner_id.id})

        if dict_content.get('simple_pdf_invoice_number_ids'):
            for _invoice_fields in dict_content.get('simple_pdf_invoice_number_ids'):
                _invoice_fields[-1].update({'partner_id': partner_id.id})

        partner_id.write(dict_content)

