# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EdiEnvelopeRest(models.Model):
    _inherit = "edi.envelope"

    def send(self):
        """Send the envelope via FTP"""
        if self.protocol_id.id == self.env.ref('edi_protocol_ftp.ftp_edi_protocol_type').id:
            pass
        return super(EdiEnvelopeRest, self).send()

    @api.model
    def receive(self):
        if self.protocol_id.id == self.env.ref('edi_protocol_ftp.ftp_edi_protocol_type').id:
            pass
        return super(EdiEnvelopeRest, self).receive()
