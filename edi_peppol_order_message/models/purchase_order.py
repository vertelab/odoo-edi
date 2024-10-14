from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def trigger_save(self):
        self.env['peppol.message'].pack(self)