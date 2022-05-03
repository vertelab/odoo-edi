from odoo import fields, models
from odoo.tools.translate import _


class peppol_wizard(models.TransientModel):
    _name = 'peppol.wizard'
    _description = 'A dialog-box wizard for Peppol'
    #_columns = {
    #    'text': fields.text(),
    #}
    text = fields.Text()
    state = fields.Text()

peppol_wizard()
