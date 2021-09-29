# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEngine(models.Model):
    _name = "edi.engine"
    _description = "Engine for EDI functionality"

    # calls logging

    @api.model
    def run_out(self, route=False, envelope=False):
        """Start processing messages"""
        # TODO: add envelope, finish function
        domain = []
        if route:
            domain.append(('route_id', '=', route))
        self.env["edi.route"].search(domain).run_out()
