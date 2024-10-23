# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Edi Envelope'

    route_id = fields.Many2one("edi.route", string="Edi Route")
