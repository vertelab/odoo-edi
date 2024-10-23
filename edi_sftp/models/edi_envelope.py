# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

import paramiko
import os
import base64
from io import BytesIO

class EdiEnvelope(models.Model):
    _inherit = 'edi.envelope'
    _description = 'Edi Envelope'

    def fetch_files(self):
        private_key_path = "/opt/odoo/.ssh/id_rsa"  # Need a private ssh key that odoo can access, meaning it has ownership of
        remote_directory = "/home/josef/recieve/"

        # Load the private key
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

        client = paramiko.SSHClient()

        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server using the private key
        client.connect(hostname="10.190.229.229", port=22, username="josef", pkey=private_key)

        sftp = client.open_sftp()

        try:
            sftp.chdir(remote_directory)  # Test if remote_directory exists
        except FileNotFoundError:
            _logger.info(f"Remote directory '{remote_directory}' does not exist.")

       # 1 : Get the new files name in the directory
        recieve_directory_files = sftp.listdir()

        # 2 : Use the retrived file names and read each and everyone
        for new_file in recieve_directory_files:
            remote_file_path = f"{remote_directory}{new_file}"
            if '.' in new_file:
                file_extension = new_file.split('.')[1]
                if file_extension == "xml":
                    with sftp.file(remote_file_path, mode='r') as remote_file:
                        file_content = remote_file.read().decode('utf-8')

                        message_xml_data = base64.b64encode(file_content.encode('utf-8'))

                        self.env['edi.envelope'].create({
                            "payload" : message_xml_data,
                            "payload_filename" : new_file
                        })

        # TODO 3 : After reaciving them, put them into a another folder, meaning they are read and will not be flagged

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
                    