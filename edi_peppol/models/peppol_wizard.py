from odoo import fields, models
from odoo.tools.translate import _


# TODO: This entire class and view may be entierly unessesary and unused.
class peppol_wizard(models.TransientModel):
    _name = 'peppol.wizard'
    _description = 'A dialog-box wizard for Peppol'
    #_columns = {
    #    'text': fields.text(),
    #}
    text = fields.Text()
    state = fields.Text()

peppol_wizard()
