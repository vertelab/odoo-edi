import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def ash_kom_office_get(self, office_code):
        """
        Relies on that office_code does not exist in database yet.
        Adds a new hr.department in database with office_code.
        """
        hr_department_obj = self.env['hr.department'].search([
            (
                'office_code',
                '=',
                office_code
            )
        ])

        if not hr_department_obj:
            hr_department_obj = self.env['hr.department'].create({
                'name': office_code,
                'office_code': office_code
            })

        route = self.env.ref("edi_af_aisf_ash_kom.ash_kom_route")
        vals = {
            'name': 'ASH KOM get all',
            'edi_type': self.env.ref('edi_af_aisf_ash_kom.ash_kom_get_all').id,
            'model': hr_department_obj._name,
            'res_id': hr_department_obj.id,
            'route_id': route.id,
            'route_type': 'edi_af_ash_kom',
        }
        message = self.env['edi.message'].create(vals)
        message.sudo().pack()
        route.sudo().run()