from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    edi_code = fields.Char(
        string="EDI Code",
        help="EDI interchange identifier for this partner",
        index=True
    )

    _sql_constraints = [
        ('edi_code_unique', 'unique(edi_code)',
         'EDI Code must be unique per partner!')
    ]