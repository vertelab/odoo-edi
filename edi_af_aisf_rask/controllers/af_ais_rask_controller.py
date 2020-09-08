import logging

from odoo import models, api

_logger = logging.getLogger(__name__)

class ais_as_rask_controller(models.Model):
    _inherit = 'res.partner'

    @api.model
    def rask_controller(self, customer_id, social_security_number, former_social_security_number, message_type):
        _logger.info("ais_as_rask_controller.rask_controller(): customerId: %s socialSecurityNumber %s formerSocialSecurityNumber %s messageType %s" % (customer_id, social_security_number, former_social_security_number, message_type))
        if message_type == "PersonnummerByte":
            res_partner_obj = self.env['res.partner'].search([('customer_id', '=', customer_id)])
            if res_partner_obj:
                res_partner_obj.company_registry = social_security_number
            else:
                pass
        else:
            # Här ska RASK anropas via IPF enligt konstens alla regler :)
            _logger.info("ais_as_rask_controller.rask_controller(): messageType %s" % message_type)

            record = self.env['res.partner'].search([('customer_id', '=', customer_id)])
            if not record:
                record = self.env['res.partner'].create({ 'name': "no customer exists"})
                record.customer_id = customer_id

            route = self.env.ref("edi_af_aisf_rask.rask_route")
            #'name': 'EDI AF AIS-F RASK Get all message',
            vals = {
                'name': message_type,
                'edi_type': self.env.ref('edi_af_aisf_rask.rask_get_all').id,
                'model': record._name,
                'res_id': record.id,
                'route_id': route.id,
                'route_type': 'edi_af_as_rask',
            }
            message = self.env['edi.message'].create(vals)
            message.pack()
            route.run()


