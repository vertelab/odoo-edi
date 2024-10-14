from odoo import api, fields, models, _

class AccountTax(models.Model):
    _inherit = 'account.tax'

    classified_tax_category = fields.Selection([('ae', 'AE'), ('e', 'E'), ('s', 'S'), ('z', 'Z'), ('g','G'), ('o', 'O'), ('k', 'K'), ('l', 'L'), ('m','M'), ('b', 'B')], help="https://docs.peppol.eu/poacc/billing/3.0/codelist/UNCL5305/")