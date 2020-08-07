# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
# from datetime import datetime, timedelta
import json
import copy
# import pytz

import logging
_logger = logging.getLogger(__name__)

jn_trans_dict = {'J': True, 'j': True, 'N': False, 'n': False}

class AGController(http.Controller):

    @http.route('/v1/arbetsgivareMeddelande', type='json', auth="public", methods=['POST'], csrf=False)
    def post_ag_message(self, **kwargs):
        """Creates a new res.partner of type employer."""
        _logger.warn(request.httprequest.data)
        
        message = json.loads(request.httprequest.data)
        
        _logger.warn(message)

        if not message:
            return Response({"message": "Bad request: No message"}, status=400)

        vals = {}
        visit_adress = {}
        delivery_adress = {}
        child_ids = []
        sni_ids = []

        # hardcoded values
        vals['company_type'] = "company"

        # message.employer
        vals['customer_id'] = message.get('arbetsgivare').get('kundnr')
        vals['name'] = message.get('arbetsgivare').get('namn')
        vals['cfar'] = message.get('arbetsgivare').get('cfar')
        # vals[''] = message.get('arbetsgivare').get('antalAnstallda')
        # vals[''] = message.get('arbetsgivare').get('storlekklassKod')
        # vals[''] = message.get('arbetsgivare').get('storlekklassText') 
        # vals[''] = message.get('arbetsgivare').get('verksamhetsbeskr')
        # vals[''] = message.get('arbetsgivare').get('internInformation')
        vals['employer_class'] = str(message.get('arbetsgivare').get('arbetsgivarklass'))
        # vals[''] = message.get('arbetsgivare').get('yrkesgrupperBeskr')
        # vals[''] = message.get('arbetsgivare').get('overenskOrderKod')
        # vals[''] = message.get('arbetsgivare').get('overenskOrderText')
        # vals[''] = message.get('arbetsgivare').get('internetAg')
        # vals[''] = message.get('arbetsgivare').get('kontorKod')
        # vals[''] = message.get('arbetsgivare').get('senasteKontaktdatum')
        # vals[''] = message.get('arbetsgivare').get('senasteKontaktKontor')
        # vals[''] = message.get('arbetsgivare').get('senasteKontaktSign')
        vals['active'] = not jn_trans_dict[message.get('arbetsgivare').get('raderad')] 
        # vals[''] = message.get('arbetsgivare').get('skapadAv')
        # vals[''] = message.get('arbetsgivare').get('aktiv') #???
        
        vals['email'] = message.get('arbetsgivare').get('epost')
        vals['website'] = message.get('arbetsgivare').get('hemsida')
        vals['phone'] = message.get('arbetsgivare').get('telnr')
        vals['fax'] = message.get('arbetsgivare').get('faxnr')

        if message.get('arbetsgivare').get('besoksadress'):
            visit_adress['name'] = 'Besoksadress'
            visit_adress['type'] = 'visitation address'
            visit_adress['street'] = message.get('arbetsgivare').get('besoksadress')
            visit_adress['zip'] = message.get('arbetsgivare').get('besoksadressPostnr')
            visit_adress['city'] = message.get('arbetsgivare').get('besoksadressPostort')
            # TODO: Make sure this doesnt break with bad input
            visit_adress['state_id'] = request.env["res.country.state"].search([('code', '=', message.get('arbetsgivare').get('besoksadressKommunKod'))]).id
            visit_adress['country_id'] = request.env["res.country"].with_context(lang='sv_SE').search([('name', '=ilike', message.get('arbetsgivare').get('besoksadressLand'))]).id 
            child_ids.append((0, 0, visit_adress))

        if message.get('arbetsgivare').get('utdelningsadress'):
            delivery_adress['name'] = 'Utdelningsadress'
            delivery_adress['type'] = 'delivery'
            delivery_adress['street'] = message.get('arbetsgivare').get('utdelningsadress')
            delivery_adress['zip'] = message.get('arbetsgivare').get('utdelningsadressPostnr')
            delivery_adress['city'] = message.get('arbetsgivare').get('utdelningsadressPostort')
            # TODO: Make sure this doesnt break with bad input
            delivery_adress['state_id'] = request.env["res.country.state"].search([('code', '=', message.get('arbetsgivare').get('utdelningsadressKommunKod'))]).id
            delivery_adress['country_id'] = request.env["res.country"].with_context(lang='sv_SE').search([('name', '=ilike', message.get('arbetsgivare').get('utdelningsadressLand'))]).id 
            child_ids.append((0, 0, delivery_adress))

        _logger.warn("Do we get here?!")

        # message.employer.contacts
        # loop through contact persons and create command list
        for child_contact in message.get('arbetsgivare').get('kontaktPersonList'):
            cc_dict = {}
            # child_contact.get('id')
            cc_dict['name'] = child_contact.get('fornamn') + ' ' + child_contact.get('efternamn')
            # search for title and use existing one if there is one
            cc_title = request.env["res.partner.title"].search([('name', '=ilike', child_contact.get('befattning'))])
            if cc_title:
                cc_dict['title'] = [(4, cc_title.id, 0)]
            # else, create new title
            else:
                cc_dict['title'] = [(0,0, { 'name': child_contact.get('befattning')})]
            cc_dict['email'] = child_contact.get('epost')
            cc_dict['phone'] = child_contact.get('telefon')
            cc_dict['mobile'] = child_contact.get('mobil')
            cc_dict['comment'] = child_contact.get('beskrivning')
            # cc_dict['???'] = child_contact.get('typ')
            child_ids.append((0, 0, copy.copy(cc_dict)))

        # message.employer.SNI
        # loop through SNI list and create command list
        for sni in message.get('arbetsgivare').get('sniList'):
            sni_obj = request.env["res.sni"].sudo().search([('name', '=', sni.get('sniKod'))])
            if sni_obj:
                sni_ids.append((4, sni_obj.id, 0))
            else:
                return Response("SNI code does not exist: %s" % sni.get('sniKod'), status=400)

        # message.employer.SSYK
        # TODO: implement loop for SSYK

        vals['child_ids'] = child_ids
        vals['sni_ids'] = sni_ids

        _logger.warn('edi_af_ag: vals: %s' % vals)

        # try:
        ag = request.env['res.partner'].sudo().create(vals)
        _logger.warn('edi_af_ag: ag: %s' % ag)
        return Response("OK!", status=200)
        # except:
        #     return Response("Could not create AG!", status=400)

    @http.route('/v1/arbetsgivareMeddelande', type='http', auth="public", methods=['PUT'])
    def put_ag_message(self, start=False, stop=False, duration=False, type_id=False, channel=False, location=False, max_depth=1, **kwargs):
        pass
