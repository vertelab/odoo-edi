import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class ais_as_rask_controller(models.Model):
    _inherit = 'hr.department'

    @api.model
    def ash_kom_controller(self, office_code, message_type):
        _logger.debug(
            "called with: office_code" % office_code)

        hr_department_obj = self.env['hr.department'].search([('office_code','=',office_code)])

        route = self.env.ref("edi_af_aisf_ash_kom.ash_kom_get_all")
        vals = {
            'name': 'ASH KOM get all',
            'edi_type': self.env.ref('edi_af_aisf_ash_kom.ash_kom_get_all').id,
            'model': hr_department_obj._name,
            'res_id': hr_department_obj.id,
            'route_id': route.id,
            'route_type': 'edi_af_ash_kom',
        }
        message = self.env['edi.message'].create(vals)
        message.pack()
        route.run()