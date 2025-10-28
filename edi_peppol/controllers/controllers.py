# -*- coding: utf-8 -*-
import requests
import base64
from odoo import http, _
from odoo.http import request


class PeppolController(http.Controller):

    @http.route('/punchout/return', type='http', auth='public', methods=['POST', 'GET'], csrf=False, website=True)
    def punchout_return(self, **post):
        """Supplier posts shopping cart XML here"""

        if request.httprequest.method == 'POST':
            # Get the base64 encoded XML
            xml_base64 = post.get('return_object_base64')

            if xml_base64:
                # Remove line breaks from base64 string
                xml_base64_clean = xml_base64.replace('\r\n', '').replace('\n', '').replace('\r', '')

                # Create file upload wizard to process the envelope
                wizard = request.env['file.upload.envelope.wizard'].sudo().create({
                    'file_data': xml_base64_clean,
                    'file_name': 'punchout_catalogue.xml',  # Add filename
                })

                # Process (calls unpack which eventually calls _unpack_punch_out)
                wizard.unpack()

        # Render success template
        return request.render('edi_peppol.punchout_success')