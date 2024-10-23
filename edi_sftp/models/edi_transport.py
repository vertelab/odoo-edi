# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiTransport(models.Model):
    _inherit = 'edi.transport'
    _description = 'Edi Transport'

    type = fields.Selection(selection_add=[('sftp', 'SFTP')])
    name = fields.Char(name="Name")
    recieve_sftp_url = fields.Char(string="Recieve Url")
    send_sftp_url = fields.Char(string="Send Url")

    def send_envelope(self):
        if self.type == "sftp":
            pass
        else:
            super().send_envelope()
        

    def recieve_envelope(self):
        pass