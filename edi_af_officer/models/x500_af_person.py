import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class af_person_controller(models.Model):
    _inherit = 'res.users'

    @api.model
    def af_person_get_all(self, signature):
        """
        Relies on that office_code does not exist in database yet.
        Adds a new hr.department in database with office_code.
        """
        route = self.env['edi.route'].sudo().search([
            (
                'id',
                '=',
                self.env['ir.model.data'].xmlid_to_res_id('edi_af_officer.get_all_officers_route')
            )
        ])

        record = self.env['res.users'].sudo().search([('login', '=', signature)])

        vals = {
            'name': 'get office msg',
            'edi_type': self.env.ref('edi_af_officer.get_all_officers').id,
            'model': record._name,
            'res_id': record.id,
            'route_id': route.id,
            'route_type': 'edi_af_officer',
        }

        message = self.env['edi.message'].sudo().create(vals)
        message.pack()
        route.run()

    @api.model
    def af_person_get(self, signature):
        """
        Relies on that office_code does not exist in database yet.
        Adds a new hr.department in database with office_code.
        """
        route = self.env['edi.route'].sudo().search([
            (
                'id',
                '=',
                self.env['ir.model.data'].xmlid_to_res_id(
                    'edi_af_officer.get_officer_route'
                )
            )
        ])

        record = self.env['res.users'].sudo().search([('login', '=', signature)])

        vals = {
            'name': 'get office msg',
            'edi_type': self.env.ref('edi_af_officer.get_officer').id,
            'model': record._name,
            'res_id': record.id,
            'route_id': route.id,
            'route_type': 'edi_af_officer',
        }

        message = self.env['edi.message'].sudo().create(vals)
        message.pack()
        route.run()