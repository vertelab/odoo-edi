# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

import paramiko
import os
import base64
from io import BytesIO


class EdiTransport(models.Model):
    _inherit = 'edi.transport'
    _description = 'Edi Transport'

    type = fields.Selection(selection_add=[('sftp', 'SFTP')])
    name = fields.Char(name="Name")
    recieve_sftp_url = fields.Char(string="Recieve Url", help="IP:Directory")
    send_sftp_url = fields.Char(string="Send Url", help="IP:Directory")

    def send_envelope(self):
        if self.type == "sftp":
            _logger.info('Something happens with SFTP')
            _logger.info(f'{self.recieve_sftp_url}')
            _logger.info(f'{self.send_sftp_url}')
            pass
        else:
            super().send_envelope()

    def send_payload(self, payload, payload_filename):
        if self.type == "sftp":

            ip = self.send_sftp_url.split(':')[0]
            remote_directory = self.send_sftp_url.split(':')[1]

            private_key_path = "/opt/odoo/.ssh/id_rsa"  # Need a private ssh key that odoo can access, meaning it has ownership of

            # Load the private key
            private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

            client = paramiko.SSHClient()

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the server using the private key
            client.connect(hostname=ip, port=22, username="josef", pkey=private_key)

            sftp = client.open_sftp()

            try:
                sftp.chdir(remote_directory)  # Test if remote_directory exists
            except FileNotFoundError:
                _logger.info(_(f"Remote directory '{remote_directory}' does not exist"))

            # Upload the file
            path = f'{remote_directory}{payload_filename}'
            _logger.info(path)

            #print(f"Uploading '{local_file_path}' to '{remote_file_path}'...")
            sftp.put(local_file_path, remote_file_path)

            # Close the SFTP session and SSH client
            sftp.close()
            client.close()
        else:
            super().send_envelope()
        

    def recieve_envelope(self):
        pass