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

xmlid_module="__ais_import__"


class AGController(http.Controller):

    @http.route('/v1/arbetsgivareMeddelande', type='json', auth="public", methods=['POST'], csrf=False)
    def post_ag_message(request, **kwargs):
        """Creates a new res.partner of type employer/organisation."""
        _logger.warn(request.httprequest.data)
        
        message = json.loads(request.httprequest.data)
        
        _logger.warn(message)

        if not message:
            return Response({"message": "Bad request: No message"}, status=400)

        ag_dict = mapping(message.get('arbetsgivare'))
        
        org_dict = mapping(message.get('arbetsgivare').get('organisation'))

        ag = request.env['res.partner'].sudo().create(ag_dict)
        org_dict.update({'child_ids': [(0,0,ag.id)]})
        ag = request.env['res.partner'].sudo().create(org_dict)

        _logger.warn('edi_af_ag: ag: %s' % ag)
        return Response("OK!", status=200)
        # except:
        #     return Response("Could not create AG!", status=400)

    @http.route('/v1/arbetsgivareMeddelande', type='http', auth="public", methods=['PUT'])
    def put_ag_message(request, start=False, stop=False, duration=False, type_id=False, channel=False, location=False, max_depth=1, **kwargs):
        """Updates a res.partner of type employer/organisation."""
        _logger.warn(request.httprequest.data)
        
        message = json.loads(request.httprequest.data)
        
        _logger.warn(message)

        if not message:
            return Response({"message": "Bad request: No message"}, status=400)

        ag_dict = mapping(message.get('arbetsgivare'))
        
        org_dict = mapping(message.get('arbetsgivare').get('organisation'))

        ag_xmlid = "%s.part_emplr_%s" % (xmlid_module, message.get('arbetsgivare').get('kundnr'))
        org_xmlid = "%s.part_org_%s" % (xmlid_module, message.get('arbetsgivare'))

        ag_id = request.env['ir.model.data'].xmlid_to_res_id(ag_xmlid)
        org_id = request.env['ir.model.data'].xmlid_to_res_id(org_xmlid)

        #clear out old visitation address, sni etc

        request.env['res.partner'].browse(ag_id).write(ag_dict)
        request.env['res.partner'].browse(org_id).write(org_dict)


        _logger.warn('edi_af_ag: ag: %s org: %s' % (ag_dict, org_dict))
        return Response("OK!", status=200)

    def mapping(request, unmapped_dict):
        vals = {}
        visit_adress = {}
        vals = {}
        child_ids = []
        sni_ids = []
        ssyk_ids = []


        # hardcoded values
        vals['company_type'] = "company"
        vals['is_employer'] = True

        # message.employer
        vals['customer_id'] = unmapped_dict.get('kundnr')
        
        
        if unmapped_dict.get('cfar'):
            vals['name'] = unmapped_dict.get('namn')
            vals['cfar'] = unmapped_dict.get('cfar')
        elif unmapped_dict.get('orgnr'):
            vals['name'] = unmapped_dict.get('orgnamn')
            vals['company_registry'] = unmapped_dict.get('orgnr')

        vals['customer_since'] = unmapped_dict.get('regdatum')
        vals['comment'] = unmapped_dict.get('verksamhetsbeskr') #not mapped in data loader yet

        # vals[''] = unmapped_dict.get('antalAnstallda')
        # vals[''] = unmapped_dict.get('storlekklassKod')
        # vals[''] = unmapped_dict.get('storlekklassText') 
        # vals[''] = unmapped_dict.get('verksamhetsbeskr')
        # vals[''] = unmapped_dict.get('internInformation')
        vals['employer_class'] = str(unmapped_dict.get('arbetsgivarklass'))
        # vals[''] = unmapped_dict.get('yrkesgrupperBeskr')
        # vals[''] = unmapped_dict.get('overenskOrderKod')
        # vals[''] = unmapped_dict.get('overenskOrderText')
        # vals[''] = unmapped_dict.get('internetAg')
        # vals[''] = unmapped_dict.get('kontorKod')
        # vals[''] = unmapped_dict.get('senasteKontaktdatum')
        # vals[''] = unmapped_dict.get('senasteKontaktKontor')
        # vals[''] = unmapped_dict.get('senasteKontaktSign')
        vals['active'] = not jn_trans_dict[unmapped_dict.get('raderad')] 
        # vals[''] = unmapped_dict.get('skapadAv')
        # vals[''] = unmapped_dict.get('aktiv') #???
        
        vals['email'] = unmapped_dict.get('epost')
        vals['website'] = unmapped_dict.get('hemsida')
        vals['phone'] = unmapped_dict.get('telnr')
        vals['fax'] = unmapped_dict.get('faxnr')

        if unmapped_dict.get('besoksadress'):
            visit_adress['name'] = 'Besoksadress'
            visit_adress['type'] = 'visitation address'
            visit_adress['street'] = unmapped_dict.get('besoksadress')
            visit_adress['zip'] = unmapped_dict.get('besoksadressPostnr')
            visit_adress['city'] = unmapped_dict.get('besoksadressPostort')
            # TODO: Make sure this doesnt break with bad input
            visit_adress['state_id'] = request.env["res.country.state"].search([('code', '=', unmapped_dict.get('besoksadressKommunKod'))]).id
            visit_adress['country_id'] = request.env["res.country"].with_context(lang='sv_SE').search([('name', '=ilike', unmapped_dict.get('besoksadressLand'))]).id 
            child_ids.append((0, 0, visit_adress))

        if unmapped_dict.get('utdelningsadress'):
            vals['name'] = 'Utdelningsadress'
            vals['type'] = 'delivery'
            vals['street'] = unmapped_dict.get('utdelningsadress')
            vals['zip'] = unmapped_dict.get('utdelningsadressPostnr')
            vals['city'] = unmapped_dict.get('utdelningsadressPostort')
            # TODO: Make sure this doesnt break with bad input
            vals['state_id'] = request.env["res.country.state"].search([('code', '=', unmapped_dict.get('utdelningsadressKommunKod'))]).id
            vals['country_id'] = request.env["res.country"].with_context(lang='sv_SE').search([('name', '=ilike', unmapped_dict.get('utdelningsadressLand'))]).id 
            

        _logger.warn("Do we get here?!")

        # message.employer.contacts
        # loop through contact persons and create command list
        for child_contact in unmapped_dict.get('kontaktPersonList'):
            cc_dict = {}
            # child_contact.get('id')
            cc_dict['firstname'] = child_contact.get('fornamn') 
            cc_dict['lastname'] = child_contact.get('efternamn')
            # search for title and use existing one if there is one
            # #cc_title = request.env["res.partner.title"].search([('name', '=ilike', child_contact.get('befattning'))])
            # if cc_title:
            #     cc_dict['title'] = [(4, cc_title.id, 0)]
            # # else, create new title
            # else:
            #     cc_dict['title'] = [(0,0, { 'name': child_contact.get('befattning')})]
            cc_dict['email'] = child_contact.get('epost')
            cc_dict['phone'] = child_contact.get('telefon')
            cc_dict['mobile'] = child_contact.get('mobil')
            cc_dict['comment'] = child_contact.get('beskrivning') #not mapped in data loader yet
            # cc_dict['???'] = child_contact.get('typ')
            child_ids.append((0, 0, copy.copy(cc_dict)))

        # message.employer.SNI
        # loop through SNI list and create command list
        for sni in unmapped_dict.get('sniList'):
            external_xmlid = "res_sni.sni_%s" % sni.get('sniKod')
            sni_id = request.env['ir.model.data'].xmlid_to_res_id(external_xmlid)
            if sni_id:
                sni_ids.append((4, sni_id))
            else:
                return Response("SNI code does not exist: %s" % sni.get('sniKod'), status=400)

        for ssyk in unmapped_dict.get('yrkesgruppList'):
            external_xmlid = "res_ssyk.ssyk_%s" % sni.get('ssyk')
            ssyk_id = request.env['ir.model.data'].xmlid_to_res_id(external_xmlid)
            if ssyk_id:
                ssyk_ids.append((4, ssyk_id))
            else:
                return Response("SSYK code does not exist: %s" % ssyk.get('ssyk'), status=400)

        # message.employer.SSYK
        # TODO: implement loop for SSYK             

        vals['child_ids'] = child_ids
        vals['sni_ids'] = sni_ids
        vals['ssyk_ids'] = ssyk_ids

        _logger.warn('edi_af_ag: vals: %s' % vals)

        return vals

        # try:
