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
from odoo import models, api, _
import ast
import json

import logging

_logger = logging.getLogger(__name__)

LOCAL_TZ = 'Europe/Stockholm'


class edi_message(models.Model):
    _inherit = 'edi.message'

    @api.one
    def unpack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_rask.rask_get_all').id:
            body = json.loads(self.body)
            customer_id = body.get('arbetssokande').get('sokandeId')
            # TODO: hur hanterat fornamn oc efternamn map name?
            # fornamn = body.get('arbetssokande').get('fornamn')
            # efternamn = body.get('arbetssokande').get('efternamn')
            res_partner_obj = self.env['res.partner'].search([('customer_id', '=', customer_id)])
            # TODO: hantera hemkommunKod
            office_obj = self.env['res.partner'].search([('office_code', '=', body.get('kontor').get('kontorsKod'))])
            # TODO: hantera office
            # TODO: hantera tillgång till bil, notifiering får vi men REST-api för matchning måste anropas
            jobseeker_dict = {
                'firstname': body.get('arbetssokande').get('fornamn'),
                'lastname': body.get('arbetssokande').get('efternamn'),
                'company_registry': body.get('arbetssokande').get('personnummer'),
                'customer_since': body.get('processStatus').get('aktuellSedanDatum'),
                'share_info_with_employers': body.get('medgivande').get('infoTillArbetsgivare'),
                'phone': body.get('kontaktuppgifter').get('telefonBostad'),
                'work_phone': body.get('kontaktuppgifter').get('telefonArbetet'),
                'mobile': body.get('kontaktuppgifter').get('telefonMobil'),
                'jobseeker_category': body.get('kontakt').get('sokandekategoriKod'),
                'deactualization_date': body.get('processStatus').get('avaktualiseringsDatum'),
                'deactualization_reason': body.get('processStatus').get('avaktualiseringsOrsaksKod'),
                'email': body.get('kontaktuppgifter').get('epost'),
                'office': office_obj.id,
            }
            res_partner_obj.write(jobseeker_dict)

            for address in body.get('kontaktuppgifter').get('adresser'):
                streetaddress = address.get('gatuadress')
                streetadress_array = streetaddress.split(",")
                if len(streetadress_array) == 1:
                    street = streetadress_array[0]
                    street2 = None
                elif len(streetadress_array) > 1:
                    street = streetadress_array[1]
                    street2 = streetadress_array[0]
                zip = address.get('postnummer')
                city = address.get('postort')
                # TODO: hur hantera landsadress?

                if address.get('adressTyp') == 'FBF':
                    res_partner_obj.street = street
                    res_partner_obj.street2 = street2
                    res_partner_obj.zip = zip
                    res_partner_obj.city = city
                    _logger.info("edi_af_aisf_rask.edit_message.upack() - adressTyp = FBF")
                elif address.get('adressTyp') == 'EGEN' or address.get('adressTyp') == 'UTL':
                    _logger.info("edi_af_aisf_rask.edit_message.upack() - adressTyp = EGEN or UTL")
                    given_address_object = self.env['res.partner'].search([('parent_id', '=', res_partner_obj.id)])
                    if not given_address_object:
                        _logger.info("edi_af_aisf_rask.edit_message.upack() - no given address object exists")
                        given_address_dict = {
                            'parent_id': res_partner_obj.id,
                            'street': street,
                            'street2': street2,
                            'zip': zip,
                            'city': city,
                            'type': 'given address',
                        }
                        self.env['res.partner'].create(given_address_dict)
                        _logger.info("edi_af_aisf_rask.edit_message.upack() - given address object created")
                    else:
                        given_address_object.street = street
                        given_address_object.street2 = street2
                        given_address_object.zip = zip
                        given_address_object.city = city
                        _logger.info("edi_af_aisf_rask.edit_message.upack() - given address object exists")

            _logger.info("edi_af_aisf_rask.edit_message.upack() - res.partner-object updated")

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_rask.rask_get_all').id:
            obj = self.model_record
            _logger.info("edi_af_aisf_rask.edit_message.pack() has been called, customer_id: %s" % obj.customer_id)

            self.body = self.edi_type.type_mapping.format(
                path="ais-f-arbetssokande/v1/arbetssokande/{customer_id}/anpassad?resurser=alla".format(
                    customer_id=obj.customer_id)
            )
            envelope = self.env['edi.envelope'].create({
                'name': 'RASK all information request',
                'route_id': self.route_id.id,
                'route_type': self.route_type,
                'edi_message_ids': [(6, 0, [self.id])]
            })
        else:
            super(edi_message, self).pack()
