# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    edi_message_ids = fields.One2many(comodel_name='edi.message', related='purchase_id.edi_message_ids')
    edi_message_count = fields.Integer(related='purchase_id.edi_message_count')

    # def action_view_edi_messages(self):
    #     return {
    #         'name': _('EDI Messages'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'edi.message',
    #         'view_mode': 'list,form',
    #         'domain': [
    #             ('res_id', '=', self.id),
    #             ('res_model', '=', 'stock.picking')
    #         ],
    #     }
