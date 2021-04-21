# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
import json
import pytz
import ast

import logging

_logger = logging.getLogger(__name__)


class edi_message(models.Model):
    _inherit = 'edi.message'
    # obj = False

    @api.one
    def unpack(self):
        _logger.warning("KROM CHECK UNPACK")
        if self.edi_type.id == self.env.ref('edi_af_ais_bos.krom_postcode').id:
            # decode string and convert string to tuple, convert tuple to dict
            if False:
                body = json.loads(self.body.decode("utf-8"))
                _logger.warning("called with: bodyz %s " % body)

                # Get values Krom
                kromtype = body.get('kromTyp')
                _logger.warning("called with: kromtype %s " % kromtype)
                if kromtype:
                    self.env['res.partner'].browse(self.res_id).kromtype = kromtype  #always true
                    if kromtype == 'Krom':
                        kromtype = 'KROM'
                    if kromtype == 'KromEsf':
                        kromtype = 'KROM ESF'
                    if kromtype == 'EjKrom':
                        kromtype = 'NEJ'

                    vals = {
                        'kromtype': kromtype,
                    }
                    kromtype.write(vals)
                else:
                    pass
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        _logger.warning("KROM CHECK PACK")
        if self.edi_type.id == self.env.ref('edi_af_ais_bos.krom_postcode').id:
            if not self.model_record or self.model_record._name != 'res.partner':
                raise Warning("KROM: Attached record is not an res.partner'! {model}".format(
                    model=self.model_record and self.model_record._name or None))

            obj = self.model_record  # res.partner
            _logger.warning("called with: obj %s " % obj)
            given_address = obj.child_ids.filtered(lambda r: r.type == "given address")
            _logger.warning("called with: given_address %s " % given_address)
            if given_address:
                postcode = given_address[0].zip
                _logger.warning("called with 78: postcode %s " % postcode)
            else:
                raise Warning("Finns ingen poskod")

            path = "ais-bos-regelverk/v2/krom/kromtyp-for-postnummer"
            self.body = self.edi_type.type_mapping.format(
                path=path,  # boolean
                postnummer=postcode  # test '72130'
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'BOS KROM V2 postcode request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]})
            _logger.warning("called with: ost %s " % envelope)
        else:
            super(edi_message, self).pack()
