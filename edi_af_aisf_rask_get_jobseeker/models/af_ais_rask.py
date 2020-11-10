from odoo import models, api, _
import logging
from odoo.tools.profiler import profile


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.model
    def rask_as_get(self, customer_id):
        # Det finns ingen förteckning över vilka ändrade attribut som triggar respektive meddelandetyp.
        # Därför ska RASK anropas för varje annan meddelandetyp än PersonnummerByte (där har vi all info)
        ipf = self.env.ref('af_ipf.ipf_endpoint_rask').sudo()
        res = ipf.call(customer_id=int(customer_id))
        self.unpack(res)
    
    @api.model
    def unpack(self, res):
        if res:
            customer_id = res.get('arbetssokande').get('sokandeId')
            res_partner_obj = self.env['res.partner'].search([('customer_id', '=', customer_id), ('is_jobseeker', '=', True)])
            if res.get('processStatus').get('skyddadePersonUppgifter'):
                res_partner_obj.unlink()
                return

            if not res_partner_obj:
                # New jobseeker
                create_links = True
            else:
                create_links = False

            res_countr_state_obj = self.env['res.country.state'].search(
                [('code', '=', res.get('kontaktuppgifter').get('hemkommunKod'))])
            office_obj = self.env['hr.department'].search([('office_code', '=', res.get('kontor').get('kontorsKod'))])
            sun_obj = self.env['res.sun'].search([('code', '=', res.get('utbildning').get('sunKod'))])
            if sun_obj is None:
                sun_obj = self.env['res.sun'].search([('code', '=', '999')])

            segmenteringsval = res.get('segmentering').get('segmenteringsval')
            if segmenteringsval == "LOKAL":
                registered_through = "local office"
            elif segmenteringsval == "SJALVSERVICE":
                registered_through = "self service"
            elif segmenteringsval == "PDM":
                registered_through = "pdm"
            else:
                registered_through = None

            skat_obj = self.env['res.partner.skat'].search([('code', '=', res.get('kontakt').get('sokandekategoriKod'))])
            if skat_obj is None:
                skat_obj_id = None
            else:
                skat_obj_id = skat_obj.id

            education_level_obj =  self.env['res.partner.education_level'].search([('name', '=', res.get('utbildning').get('utbildningsniva'))])
            if education_level_obj is None:
                education_level_obj_id = None
            else:
                education_level_obj_id = education_level_obj.id

            users_obj = self.env['res.users'].search([('login', '=', res.get('kontor').get('ansvarigHandlaggareSignatur'))])
            if users_obj is None:
                users_obj_id = None
            else:
                users_obj_id = users_obj.id

            last_contact_type_string = res.get('kontakt').get('senasteKontakttyp')
            if last_contact_type_string is None:
                last_contact_type = None
            else:
                last_contact_type = last_contact_type_string[0]

            nasta_kontakttyper_list = res.get('kontakt').get('nastaKontakttyper')
            next_contact_type = None
            if len(nasta_kontakttyper_list) > 0:
                next_contact_type = nasta_kontakttyper_list[0]
                next_contact_type = next_contact_type[0]

            # TODO: hantera tillgång till bil, notifiering får vi men REST-api för matchning måste anropas

            jobseeker_dict = {
                'firstname': res.get('arbetssokande').get('fornamn'),
                'lastname': res.get('arbetssokande').get('efternamn'),
                'company_registry': res.get('arbetssokande').get('personnummer'),
                'customer_since': res.get('processStatus').get('aktuellSedanDatum'),
                'share_info_with_employers': res.get('medgivande').get('infoTillArbetsgivare'),
                'phone': res.get('kontaktuppgifter').get('telefonBostad'),
                'work_phone': res.get('kontaktuppgifter').get('telefonArbetet'),
                'mobile': res.get('kontaktuppgifter').get('telefonMobil'),
                'jobseeker_category_id': skat_obj_id,
                'deactualization_date': res.get('processStatus').get('avaktualiseringsDatum'),
                'deactualization_reason': res.get('processStatus').get('avaktualiseringsOrsaksKod'),
                'email': res.get('kontaktuppgifter').get('epost'),
                'office_id': office_obj.id,
                'state_id': res_countr_state_obj.id,
                'education_level': education_level_obj_id,
                'registered_through': registered_through,
                'sun_ids': [(6, 0, [sun_obj.id])],
                'user_id': users_obj_id,
                'sms_reminders': res.get('medgivande').get('paminnelseViaSms'),
                'next_contact': res.get('kontakt').get('nastaKontaktdatum'),
                'next_contact_time': res.get('kontakt').get('nastaKontaktTid'),
                'next_contact_type': next_contact_type,
                'last_contact': res.get('kontakt').get('senasteKontaktdatum'),
                'last_contact_type': last_contact_type,
            }
            if res_partner_obj:
                res_partner_obj.write(jobseeker_dict)
            else:
                res_partner_obj = self.env['res.partner'].create(jobseeker_dict)

            own_or_foreign_address_given = False
            for address in res.get('kontaktuppgifter').get('adresser'):
                streetaddress = address.get('gatuadress')
                if streetaddress: 
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
        
       
        # if (create_links):
        #     res_partner_obj.sync_link()

