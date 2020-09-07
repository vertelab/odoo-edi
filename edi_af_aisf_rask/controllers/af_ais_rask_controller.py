import logging

from odoo import models, api

_logger = logging.getLogger(__name__)

class ais_as_rask_controller(models.Model):
    inherit = 'res.partner'

    @api.model
    def rask_controller(self, customerId, socialSecurityNumber, formerSocialSecurityNumber, messageType):
        if messageType == "PersonnummerByte":
            res_partner_obj = self.env['res.partner'].search([('customerId', '=', customerId)])
            if res_partner_obj:
                res_partner_obj.company_registry = socialSecurityNumber
            else:
                pass
        else:
            # Här ska RASK anropas via IPF enligt konstens alla regler :)
            _logger.info("ais_as_rask_controller.rask_controller(): messageType %s" % messageType)
