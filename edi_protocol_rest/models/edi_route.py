# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiProtoRest(models.Model):
    _inherit = "edi.route"

    protocol = fields.Selection(selection_add=[('rest', 'REST')])
    rest_api = fields.Many2one(comodel_name='rest.api', string='REST API')

    def check_connection(self):
        """Check connection"""
        # TODO implement
        return False
