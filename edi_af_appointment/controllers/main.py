# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
from datetime import datetime, timedelta
import json
import simplejson
import pytz

import logging
_logger = logging.getLogger(__name__)

LOCAL_TZ = 'Europe/Stockholm'

class AppointmentController(http.Controller):

    def is_int(self, string):
        try: 
            integer = int(string)
        except:
            return False

        return integer

    def encode_bookable_occasion_id(self, occasions):
        """Encodes a recordset of occasions to an unique id that can be used in external systems.
        :param occasions: a recordset of odoo objects"""
        return '%s-%s' % occasions._ids

    def decode_bookable_occasion_id(self, occasions):
        """Decodes a string representing occasion ids to a recordset of odoo objects.
        :param occasions: A string representing occasion ids"""
        occ_list = occasions.split('-')
        res = request.env['calendar.occasion'].sudo().search([('id', 'in', occ_list)])
        
        if len(res) == len(occ_list):
            return res
        else:
            return False
        
    @http.route('/bookable-occasions', type='http', auth="public", methods=['GET'])
    def get_bookable_occasions(self, start=False, stop=False, duration=False, type_id=False, channel=False, location=False, max_depth=1, **kwargs):
        # if not ((type_id or channel) or (duration or stop) or start):
        if not (type_id and duration and stop and start):
            return Response("Bad request", status=400)
        
        type_id = self.is_int(type_id)
        
        if not type_id:
            return Response("Bad request: Invalid type_id", status=400)

        type_id = request.env['calendar.appointment.type'].sudo().search([('ipf_num', '=', type_id)])
        
        if not type_id:
            return Response("Meeting type not found", status=404)

        _logger.warn('get_bookable_occasions: type_id: %s' % type_id)

        if not channel:
            channel = type_id.channel

        # _logger.warn('get_bookable_occasions: channel: %s' % channel)

        start_time = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        stop_time = datetime.strptime(stop, "%Y-%m-%dT%H:%M:%SZ")

        # Integration gives us times in local (Europe/Stockholm) tz
        # Convert to UTC
        start_time_utc = pytz.timezone(LOCAL_TZ).localize(start_time).astimezone(pytz.utc)
        stop_time_utc = pytz.timezone(LOCAL_TZ).localize(stop_time).astimezone(pytz.utc)

        if not duration:
            duration = start_time_utc.minute - stop_time_utc.minute
        else:
            duration = self.is_int(duration)

        # _logger.warn('get_bookable_occasions: duration: %s' % duration)

        if not stop:
            stop = start_time_utc + timedelta(minutes=duration)

        # TODO: if local meeting, check location arg.

        res = request.env['calendar.occasion'].sudo().get_bookable_occasions(start_time_utc, stop_time_utc, duration, type_id, max_depth)
        
        for day in res:
            for slot in day:
                # change occasions from recordsets to an 'external' ID
                day[day.index(slot)] = self.encode_bookable_occasion_id(slot)
        
        # convert to json format
        res = json.dumps(res)
        _logger.warn('get_bookable_occasions: res: %s' % res)

        return Response(res, mimetype='application/json', status=200)

    @http.route('/bookable-occasions/reservation/<bookable_occasion_id>', type='http', csrf=False, auth="public", methods=['POST'])
    def reserve_bookable_occasion(self, bookable_occasion_id=False, **kwargs):
        occasions = self.decode_bookable_occasion_id(bookable_occasion_id)
        if not occasions:
            return Response("Bad request: Invalid id", status=400)

        res = request.env['calendar.occasion'].sudo().reserve_occasion(occasions)

        if res:
            return Response("OK, reservation created", status=201)
        else:
            return Response("ID not found", status=404)

    @http.route('/bookable-occasions/reservation/<bookable_occasion_id>', type='http', csrf=False, auth="public", methods=['DELETE'])
    def unreserve_bookable_occasion(self, bookable_occasion_id=False, **kwargs):
        # TODO: fix these error messages
        occasions = self.decode_bookable_occasion_id(bookable_occasion_id)
        if not occasions:
            return Response("ID not found", status=404)
        try:
            if request.env['calendar.appointment'].sudo().delete_reservation(occasions):
                return Response("OK, reservation deleted", status=200)
            else:
                return Response("ID not found", status=404)
        except:
            return Response("ID not found", status=404)

    @http.route('/appointments', type='http', auth="public", methods=['GET'])
    def get_appointment(self, user_id, customer_nr, prn, appointment_types, status_list, start, stop, **kwargs):
        # TODO: implement
        _logger.warn('DAER: get_appointment: %s' % 'start')
        pass

    @http.route('/appointments', type='json', auth="public", methods=['POST'])
    def create_appointment(self, bookable_occasion_id, customer_nr, **kwargs):
        # TODO: implement
        pass

    @http.route('/appointments/<model("calendar.appointment"):appointment_id>', type='http', auth="public", methods=['PUT'])
    def update_appointment(self, appointment_id, title, user_id, customer_nr, appointment_type, status, start, stop, duration, office, **kwargs):
        # TODO: implement
        if appointment_id:
            if customer_nr and appointment_type and start and stop and duration:
                values = {
                    # 'type_id' request.env
                }
            else:
                return Response("Bad request", status=400)
        else:
            return Response("Bad request: Invalid id", status=400)

    @http.route('/appointments/<appointment_id>', type='http', csrf=False, auth="public", methods=['DELETE'])
    def delete_appointment(self, appointment_id, **kwargs):
        _logger.warn('delete_appointment: args: %s' % appointment_id)
        
        appointment_id = self.is_int(appointment_id)

        if appointment_id and appointment_id > 0:
            appointment = request.env['calendar.appointment'].sudo().search([('id', '=', appointment_id)])
            if appointment:
                appointment.sudo().unlink()
                return Response("OK, deleted", status=200)
            else:
                return Response("ID not found", status=404)
        else:
            return Response("Bad request: Invalid id", status=400)
