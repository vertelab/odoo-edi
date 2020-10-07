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
            res_partner_obj = self.env['res.partner'].search([('customer_id', '=', customer_id)])

            if body.get('processStatus').get('skyddadePersonUppgifter'):
                res_partner_obj.unlink()
                return

            if (res_partner_obj.firstname == "new object" and res_partner_obj.lastname == "new object"):
                # New jobseeker
                create_links = True
            else:
                create_links = False

            res_countr_state_obj = self.env['res.country.state'].search(
                [('code', '=', body.get('kontaktuppgifter').get('hemkommunKod'))])
            office_obj = self.env['hr.department'].search([('office_code', '=', body.get('kontor').get('kontorsKod'))])
            sun_obj = self.env['res.sun'].search([('code', '=', body.get('utbildning').get('sunKod'))])
            if sun_obj is None:
                sun_obj = self.env['res.sun'].search([('code', '=', '999')])

            segmenteringsval = body.get('segmentering').get('segmenteringsval')
            if segmenteringsval == "LOKAL":
                registered_through = "local office"
            elif segmenteringsval == "SJALVSERVICE":
                registered_through = "self service"
            elif segmenteringsval == "PDM":
                registered_through = "pdm"
            else:
                registered_through = None

            skat_obj = self.env['res.partner.skat'].search([('code', '=', body.get('kontakt').get('sokandekategoriKod'))])
            if skat_obj is None:
                skat_obj_id = None
            else:
                skat_obj_id = skat_obj.id

            education_level_obj =  self.env['res.partner.education_level'].search([('name', '=', body.get('utbildning').get('utbildningsniva'))])
            if education_level_obj is None:
                education_level_obj_id = None
            else:
                education_level_obj_id = education_level_obj.id

            users_obj = self.env['res.users'].search([('login', '=', body.get('kontor').get('ansvarigHandlaggareSignatur'))])
            if users_obj is None:
                users_obj_id = None
            else:
                users_obj_id = users_obj.id

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
                'jobseeker_category_id': skat_obj_id,
                'deactualization_date': body.get('processStatus').get('avaktualiseringsDatum'),
                'deactualization_reason': body.get('processStatus').get('avaktualiseringsOrsaksKod'),
                'email': body.get('kontaktuppgifter').get('epost'),
                'office_id': office_obj.id,
                'state_id': res_countr_state_obj.id,
                'education_level': education_level_obj_id,
                'registered_through': registered_through,
                'sun_ids': [(6, 0, [sun_obj.id])],
                'user_id': users_obj_id,
                'sms_reminders': body.get('medgivande').get('paminnelseViaSms'),
            }
            res_partner_obj.write(jobseeker_dict)

            own_or_foreign_address_given = False
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
                country_name = address.get('landsadress')
                country_obj_id = None
                if country_name is not None:
                    country_obj = self.env['res.country'].with_context(lang='sv_SE').search(
                        [('name', '=', country_name)])
                    if country_obj is not None:
                        country_obj_id = country_obj.id

                if address.get('adressTyp') == 'FBF':
                    res_partner_obj.street = street
                    res_partner_obj.street2 = street2
                    res_partner_obj.zip = zip
                    res_partner_obj.city = city
                    res_partner_obj.country_id = country_obj_id
                elif address.get('adressTyp') == 'EGEN' or address.get('adressTyp') == 'UTL':
                    own_or_foreign_address_given = True
                    given_address_object = self.env['res.partner'].search([('parent_id', '=', res_partner_obj.id)])
                    if not given_address_object:
                        given_address_dict = {
                            'parent_id': res_partner_obj.id,
                            'street': street,
                            'street2': street2,
                            'zip': zip,
                            'city': city,
                            'type': 'given address',
                            'country_id': country_obj_id,
                        }
                        self.env['res.partner'].create(given_address_dict)
                    else:
                        given_address_object.street = street
                        given_address_object.street2 = street2
                        given_address_object.zip = zip
                        given_address_object.city = city
                        given_address_object.country_id = country_obj_id

            if not own_or_foreign_address_given:
                given_address_object = self.env['res.partner'].search([('parent_id', '=', res_partner_obj.id)])
                if given_address_object:
                    given_address_object.unlink()

            if (create_links):
                res_partner_obj.sync_links()

    @api.one
    def pack(self):
        if self.edi_type.id == self.env.ref('edi_af_aisf_rask.rask_get_all').id:
            obj = self.model_record

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
