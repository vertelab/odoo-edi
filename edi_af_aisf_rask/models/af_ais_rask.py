import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class ais_as_rask_controller(models.Model):
    _inherit = 'res.partner'

    @api.model
    def rask_controller(self, customer_id, social_security_number, former_social_security_number, message_type):
        _logger.debug(
            "called with: customer_id %s social_security_number: %s former_social_security_number %s message_type %s" % (
            customer_id, social_security_number, former_social_security_number, message_type))

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

    @api.model
    def update_jobseeker_from_file(self, path):
        _logger.debug("called with: Path %s" % ( path ))

        rownr = 0
        iterations = 0
        with open(path) as fh:
            for row in fh:
                if rownr == 0:
                    rownr += 1
                    continue

                customer_id = row.strip()
                self.env['res.partner'].rask_controller( customer_id, None, None, None)

                iterations += 1
                if not iterations % 500:
                    self.env.cr.commit()
                    _logger.info('%s Users updated' % iterations)