import logging
from odoo import models, api, _, fields


_logger = logging.getLogger(__name__)

class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.base"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."


    def peppol_button(self):
        _logger.warning("Clicked the Button!")
        _logger.warning(f"{self.name=}")
        #currency_row = self.env["res.currency"].browse(self.currency_id.id)
        #_logger.warning(f"{self.currency_id.name=}")

        #self.test()

        self.invoice_to_peppol()

        #_logger.warning(peppol_main.main())
        return None