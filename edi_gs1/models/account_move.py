from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_pack_edi(self):
        route_id = self.partner_id.route_id
        if not route_id:
            return None
        route_id._process_edi_route(rec=self)

