# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EdiSessionLine(models.Model):
    _name = 'edi.session.line'
    _description = 'Edi Session Line'

    message_format_id = fields.Many2one("edi.message.format")
    transport_id = fields.Many2one("edi.transport", string="Transport")
    domain = fields.Char(string="Domain")
    message_id = fields.Many2one("edi.message", string="Message")

    session_id = fields.Many2one("edi.session", string="Session")

    odoo_reference = fields.Reference(selection=[('purchase.order', "Purchase")], string="Odoo Reference", help="Is the odoo record connected to this line.")

    def pack(self):
        self.ensure_one()
        if not self.odoo_reference:
            raise UserError(_("""
Current EDI line is missing an odoo record.
Can't make an edi.message!
             """))
        return self.message_format_id.pack(self.odoo_reference, self)