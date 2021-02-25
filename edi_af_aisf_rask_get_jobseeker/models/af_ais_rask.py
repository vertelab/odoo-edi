import logging
import time

from odoo import models, api, _
from odoo.tools.profiler import profile

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def rask_as_get(self, customer_id, db_con, db_values):
        """
        Relies on that customer_id does not exist in database yet.
        Adds a new res.partner in database with customer_id.
        """
        start_time = time.time()
        res = db_con.call(customer_id=int(customer_id))
        end_time = time.time()
        time_for_call_to_rask = end_time - start_time

        if not res:
            _logger.warning("customer_id %s not found in AIS-F/RASK" % customer_id)
            return time_for_call_to_rask
        customer_id = res.get('arbetssokande',{}).get('sokandeId')
        if res.get('processStatus', {}).get('skyddadePersonUppgifter'):
            return time_for_call_to_rask

        key = res.get('kontaktuppgifter',{}).get('hemkommunKod')
        res_country_state_id = db_values['res.country.state'].get(key)

        key = res.get('kontor',{}).get('kontorsKod')
        office_id = db_values['hr.department'].get(key, False)

        key = res.get('utbildning',{}).get('sunKod')
        sun_id = db_values['res.sun'].get(key, db_values['res.sun'].get('999'))

        segmenteringsval = res.get('segmentering',{}).get('segmenteringsval')
        if segmenteringsval == "LOKAL":
            registered_through = "local office"
        elif segmenteringsval == "SJALVSERVICE":
            registered_through = "self service"
        elif segmenteringsval == "PDM":
            registered_through = "pdm"
        else:
            registered_through = False

        key = res.get('kontakt',{}).get('sokandekategoriKod')
        skat_id = db_values['res.partner.skat'].get(key, False)

        key = res.get('utbildning',{}).get('utbildningsniva')
        if key is not None:
            try:
                key_int = int(key)
                education_level_id = db_values['education_level'].get(key_int, False)
            except ValueError:
                education_level_id = 0
        else:
            education_level_id = 0

        key = res.get('kontor',{}).get('ansvarigHandlaggareSignatur')
        users_id = db_values['res.users'].get(key, False)

        last_contact_type = res.get('kontakt',{}).get('senasteKontakttyp') or False
        if last_contact_type:
            last_contact_type = last_contact_type[0]

        next_contact_type = res.get('kontakt',{}).get('nastaKontakttyper',{}) or False
        if next_contact_type:
            next_contact_type = next_contact_type[0][0]

        jobseeker_dict = {
            'firstname': res.get('arbetssokande',{}).get('fornamn','MISSING FIRSTNAME'),
            'lastname': res.get('arbetssokande',{}).get('efternamn','MISSING LASTNAME'),
            'customer_id': customer_id,
            'social_sec_nr': res.get('arbetssokande',{}).get('personnummer'),
            'customer_since': res.get('processStatus',{}).get('aktuellSedanDatum'),
            'share_info_with_employers': res.get('medgivande',{}).get('infoTillArbetsgivare'),
            'phone': res.get('kontaktuppgifter',{}).get('telefonBostad'),
            'work_phone': res.get('kontaktuppgifter',{}).get('telefonArbetet'),
            'mobile': res.get('kontaktuppgifter',{}).get('telefonMobil'),
            'jobseeker_category_id': skat_id,
            'deactualization_date': res.get('processStatus',{}).get('avaktualiseringsDatum'),
            'deactualization_reason': res.get('processStatus',{}).get('avaktualiseringsOrsaksKod'),
            'email': res.get('kontaktuppgifter',{}).get('epost'),
            'office_id': office_id,
            'state_id': res_country_state_id,
            'registered_through': registered_through,
            'user_id': users_id,
            'sms_reminders': res.get('medgivande',{}).get('paminnelseViaSms'),
            'next_contact_date': res.get('kontakt',{}).get('nastaKontaktdatum'),
            'next_contact_time': res.get('kontakt',{}).get('nastaKontaktTid'),
            'next_contact_type': next_contact_type,
            'last_contact_date': res.get('kontakt',{}).get('senasteKontaktdatum'),
            'last_contact_type': last_contact_type,
            'is_jobseeker': True
        }

        res_partner = self.env['res.partner'].create(jobseeker_dict)

        if sun_id:
                res_partner.education_ids = [(
                    6,
                    0,
                    [self.env['res.partner.education'].create({
                        'sun_id': sun_id,
                        'education_level_id': education_level_id
                    }).id]
                )]

        for address in res.get('kontaktuppgifter',{}).get('adresser',{}):
            streetaddress = address.get('gatuadress')
            if streetaddress:
                streetadress_array = streetaddress.split(",")
                if len(streetadress_array) == 1:
                    street = streetadress_array[0]
                    street2 = False
                elif len(streetadress_array) > 1:
                    street = streetadress_array[1]
                    street2 = streetadress_array[0]
                zip = address.get('postnummer')
                city = address.get('postort')
                key = address.get('landsadress')
                if key:
                    country_id = db_values['res.country'].get(key, False)
                    if country_id is False:
                        country_id = None
                else:
                    country_id = None
                if address.get('adressTyp') == 'FBF':
                    res_partner.street = street
                    res_partner.street2 = street2
                    res_partner.zip = zip
                    res_partner.city = city
                    res_partner.country_id = country_id
                elif address.get('adressTyp') == 'EGEN' or address.get('adressTyp') == 'UTL':
                    given_address_dict = {
                        'parent_id': res_partner.id,
                        'street': street,
                        'street2': street2,
                        'zip': zip,
                        'city': city,
                        'type': 'given address',
                        'country_id': country_id,
                    }
                    self.env['res.partner'].create(given_address_dict)

        return time_for_call_to_rask
