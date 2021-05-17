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
import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class edi_message(models.Model):
    _inherit = "edi.message"

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_ais_bos.krom_postcode').id:
            # decode string and convert string to tuple, convert tuple to dict
            body = json.loads(self.body.decode("utf-8"))

            # Get values Krom
            match_area = body.get("kromTyp")
            if match_area:
                self.env['res.partner'].browse(self.res_id).match_area = match_area
            else:
                pass
        else:
            super(edi_message, self).unpack()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_ais_bos.krom_postcode').id:
            if not self.model_record or self.model_record._name != 'res.partner':
                raise UserError(_("KROM: Attached record is not an res.partner'! {model}".format(
                    model=self.model_record and self.model_record._name or None)))

            obj = self.model_record  # res.partner
            given_address = obj.child_ids.filtered(lambda r: r.type == "given address")
            if given_address:
                postcode = given_address[0].zip
            else:
                raise UserError(_("Postcode field is empty or invalid"))

            path = "ais-bos-regelverk/v2/krom/kromtyp-for-postnummer"
            self.body = self.edi_type.type_mapping.format(
                path=path,  # boolean
                postnummer=postcode
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'BOS KROM V2 postcode request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]})
        else:
            super(edi_message, self).pack()
