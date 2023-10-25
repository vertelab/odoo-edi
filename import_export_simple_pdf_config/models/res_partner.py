from odoo import fields, models, api, _
import base64
from lxml import etree

EXCLUDE_FIELDS = [
    'create_date', '__last__update', 'create_uid', 'write_date', 'write_uid', 'id', '__last_update',
    'simple_pdf_test_file', 'simple_pdf_test_filename', 'simple_pdf_test_raw_text', 'simple_pdf_test_results'
]


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_simple_pdf_fields(self, model, filter_func):
        return self.env['ir.model.fields'].search([
            ('model_id.model', '=', model)
        ]).filtered(filter_func)

    def action_export_simple_pdf_config(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            active_ids = self.id
        res_partner_id = self.env['res.partner'].browse(active_ids)
        print(res_partner_id)

        simple_pdf_fields = self._get_simple_pdf_fields(
            model='res.partner',
            filter_func=lambda module: module.modules == 'account_invoice_import_simple_pdf',
        )

        data = etree.Element("partner")

        for partner_field in simple_pdf_fields.filtered(lambda x: x.name not in EXCLUDE_FIELDS):
            if res_partner_id[partner_field.name]:
                field = etree.SubElement(data, partner_field.name)
                if partner_field.ttype in ['selection', 'char']:
                    field.text = str(getattr(res_partner_id, partner_field.name))
                if partner_field.ttype == 'many2one':
                    field.text = str(getattr(res_partner_id, partner_field.name).id)
                if partner_field.ttype in ['one2many', 'many2many']:
                    relation_field_ids = self._get_simple_pdf_fields(
                        model=partner_field.relation,
                        filter_func=lambda r_field: r_field.name not in EXCLUDE_FIELDS,
                    )
                    for line in res_partner_id[partner_field.name]:
                        tree_line = etree.SubElement(field, 'line')
                        for relation_field_id in relation_field_ids:
                            if line[relation_field_id.name]:
                                if relation_field_id.ttype == 'many2one':
                                    etree.SubElement(tree_line, relation_field_id.name).text = str(
                                        line[relation_field_id.name].id
                                    )
                                else:
                                    etree.SubElement(tree_line, relation_field_id.name).text = str(
                                        line[relation_field_id.name]
                                    )

        return self._export_attachment(res_partner_id, data)

    def _export_attachment(self, res_partner_id, data):
        xml_data = etree.tostring(data, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')
        attachment = self.env['ir.attachment'].create({
            'name': f'{res_partner_id.name}_config.xml',
            'datas': base64.encodebytes(xml_data.encode('utf-8')),
            'mimetype': 'application/xml',
        })

        return {
            'type': 'ir.actions.act_url',
            'name': attachment.name,
            'url': f'/web/content/ir.attachment/{attachment.id}/datas/{attachment.name}?download=true',
        }


