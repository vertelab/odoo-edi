import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class ais_as_rask_controller(models.Model):
    _inherit = 'res.partner'

    @api.model
    def rask_controller(self, customer_id, social_security_number, former_social_security_number, message_type):
        _logger.info("called with: customer_id %s social_security_number: %s former_social_security_number %s message_type %s" % (customer_id, social_security_number, former_social_security_number, message_type))
        if message_type == "PersonnummerByte":
            # Inget anrop av RASK behöver göras eftersom allt finns i notifieringen
            res_partner_obj = self.env['res.partner'].search(
                [('customer_id', '=', customer_id), ('is_jobseeker', '=', True)])
            if res_partner_obj:
                res_partner_obj.company_registry = social_security_number
            else:
                # TODO: När allt funkar så ska det här ske i en egen metod...
                # AS saknas i AF CRM DB, hantera det som en "Nyinskrivning"
                vals = {
                    'customer_id': customer_id,
                    'firstname': "new object",
                    'lastname': "new object",
                    'is_jobseeker': True,
                }
                res_partner_obj = self.env['res.partner'].create(vals)

                route = self.env.ref("edi_af_aisf_rask.rask_route")
                vals = {
                    'name': 'RASK get all',
                    'edi_type': self.env.ref('edi_af_aisf_rask.rask_get_all').id,
                    'model': res_partner_obj._name,
                    'res_id': res_partner_obj.id,
                    'route_id': route.id,
                    'route_type': 'edi_af_as_rask',
                }
                message = self.env['edi.message'].create(vals)
                message.pack()
                route.run()
        else:
            # Det finns ingen förteckning över vilka ändrade attribut som triggar respektive meddelandetyp.
            # Därför ska RASK anropas för varje annan meddelandetyp än PersonnummerByte (där har vi all info)
            res_partner_obj = self.env['res.partner'].search(
                [('customer_id', '=', customer_id), ('is_jobseeker', '=', True)])
            if not res_partner_obj:
                # AS saknas i AF CRM DB, hantera det som en "Nyinskrivning"
                vals = {
                    'customer_id': customer_id,
                    'firstname': "new object",
                    'lastname': "new object",
                    'is_jobseeker': True,
                }
                res_partner_obj = self.env['res.partner'].create(vals)

            route = self.env.ref("edi_af_aisf_rask.rask_route")
            vals = {
                'name': 'RASK get all',
                'edi_type': self.env.ref('edi_af_aisf_rask.rask_get_all').id,
                'model': res_partner_obj._name,
                'res_id': res_partner_obj.id,
                'route_id': route.id,
                'route_type': 'edi_af_as_rask',
            }
            message = self.env['edi.message'].create(vals)
            message.pack()
            route.run()
