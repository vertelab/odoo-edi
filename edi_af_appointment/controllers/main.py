# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
from datetime import datetime, timedelta
import json
import pytz

import logging

_logger = logging.getLogger(__name__)

# DUPLICATES IN calendar_af
LOCAL_TZ = "Europe/Stockholm"
BASE_DURATION = 30.0
# RESERVED_TIMEOUT is the default time before a reservation times out.
RESERVED_TIMEOUT = 300.0


class AppointmentController(http.Controller):
    def is_int(self, string):
        """Returns a string as an integer or False in case it failed for some reason."""
        try:
            integer = int(string)
        except:
            return False

        return integer

    def encode_bookable_occasion_id(self, occasions):
        """Encodes a recordset of occasions to an unique id that can be used in external systems.
        :param occasions: a recordset of odoo objects"""
        return "-".join(occasions.mapped(lambda r: str(r.id)))

    def decode_bookable_occasion_id(self, occasions):
        """Decodes a string representing occasion ids to a recordset of odoo objects.
        :param occasions: A string representing occasion ids"""
        occ_list = occasions.split("-")
        res = request.env["calendar.occasion"].sudo().search([("id", "in", occ_list)])

        if len(res) == len(occ_list):
            return res
        else:
            return False

    @http.route(
        ["/v1/appointments/health", "/v1/appointments/ping"],
        type="http",
        auth="public",
        methods=["GET"],
    )
    def health(self, **kwargs):
        return Response("OK", status=200)

    @http.route(
        "/v1/appointments/bookable-occasions",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def get_bookable_occasions(
        self,
        start=False,
        stop=False,
        duration=False,
        type_id=False,
        channel=False,
        location=False,
        employee_user_id=False,
        profession_id=False,
        max_depth=1,
        **kwargs
    ):
        if not (type_id and duration and stop and start):
            return Response("Bad request", status=400)

        type_id = self.is_int(type_id)

        if not type_id:
            return Response("Bad request: Invalid type_id", status=400)

        type_id = (
            request.env["calendar.appointment.type"]
            .sudo()
            .search([("ipf_num", "=", type_id)])
        )

        if not type_id:
            return Response("Meeting type not found", status=404)

        if not channel:
            channel = type_id.channel

        start_time = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        stop_time = datetime.strptime(stop, "%Y-%m-%dT%H:%M:%SZ")

        if not duration:
            duration = start_time.minute - stop_time.minute
        else:
            duration = self.is_int(duration)

        if not stop:
            stop = start_time + timedelta(minutes=duration)

        if location:
            operation = (
                request.env["hr.operation"]
                .sudo()
                .search([("location_code", "=", location)])
            )
        else:
            operation = False

        occ_list = (
            request.env["calendar.occasion"]
            .sudo()
            .get_bookable_occasions(
                start_time, stop_time, duration, type_id, operation, int(max_depth)
            )
        )
        res = {}

        for day in occ_list:
            for slot in day:
                for book_occ in slot:
                    if len(book_occ) != 1:
                        book_duration = int(len(book_occ) * BASE_DURATION)
                    else:
                        book_duration = int(type_id.duration)
                    vals = {
                        # change occasions from recordsets to an 'external' ID
                        "id": self.encode_bookable_occasion_id(book_occ),
                        "appointment_title": "%sm @ %s"
                        % (book_duration, book_occ[0].start),
                        "appointment_channel": book_occ[0].channel.name,
                        "employee_name": book_occ[0].user_id.display_name
                        if book_occ[0].user_id
                        else "",
                        "employee_signature": book_occ[0].user_id.af_signature
                        if book_occ[0].user_id
                        else "",
                        "location_code": book_occ[0].operation_id.location_code
                        if book_occ[0].operation_id
                        else "",
                        "occasion_start": book_occ[0].start.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "occasion_end": book_occ[-1].stop.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "occasion_duration": book_duration,
                    }

                    # Create new list and append our value if it is the first record
                    if not res.get("bookable_occasions", False):
                        res["bookable_occasions"] = []
                        res["bookable_occasions"].append(vals)
                    else:
                        # else, just append
                        res["bookable_occasions"].append(vals)

        # convert to json format
        res = json.dumps(res)
        return Response(res, mimetype="application/json", status=200)

    @http.route(
        "/v1/appointments/bookable-occasions/reservation/<bookable_occasion_id>",
        type="http",
        csrf=False,
        auth="public",
        methods=["POST"],
    )
    def reserve_bookable_occasion(self, bookable_occasion_id=False, **kwargs):
        occasions = self.decode_bookable_occasion_id(bookable_occasion_id)
        if not occasions:
            return Response("Bad request: Invalid id", status=400)

        app = request.env["calendar.occasion"].sudo().reserve_occasion(occasions)

        if app:
            res = {
                "appointment_end_datetime": app.stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_start_datetime": app.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_length": int(app.duration * 60),
                "appointment_title": app.name or "",
                "appointment_type": app.type_id.ipf_num,
                "appointment_channel": app.channel.name or "",
                "customer_nr": app.partner_id.customer_id or "",
                "customer_name": app.partner_id.display_name or "",
                "employee_name": app.user_id.name or "",
                "employee_phone": app.user_id.phone or "",
                "employee_signature": app.user_id.name or "",
                "id": bookable_occasion_id,
                "appointment_id": app.id,
                "office_address": app.office_id.partner_id.contact_address or "",
                "office_email": app.office_id.partner_id.email or "",
                "location_code": app.operation_id.location_code or "",
                "office_code": app.office_id.office_code or "",
                "office_name": app.office_id.display_name or "",
                "status": app.state,
            }
            res = json.dumps(res)
            return Response(res, mimetype="application/json", status=201)
        else:
            return Response("ID not found", status=404)

    @http.route(
        "/v1/appointments/bookable-occasions/reservation",
        type="json",
        csrf=False,
        auth="public",
        methods=["POST"],
    )
    def reserve_bookable_occasion_json(self, bookable_occasion_id=False, **kwargs):
        message = json.loads(request.httprequest.data)
        # { "desired_time": "2019-09-30T11:00:00Z", "location_code": "71928", "appointment_length": 30, "appointment_type": 21 }

        desired_time = datetime.strptime(
            message.get("desired_time"), "%Y-%m-%dT%H:%M:%SZ"
        )
        location_code = message.get("location_code")
        appointment_length = int(message.get("appointment_length"))
        appointment_type = message.get("appointment_type")
        type_id = (
            request.env["calendar.appointment.type"]
            .sudo()
            .search([("ipf_num", "=", appointment_type)])
        )

        if not desired_time:
            return Response("Bad request: No desired_time", status=400)

        if location_code:
            operation = (
                request.env["hr.operation"]
                .sudo()
                .search([("location_code", "=", location_code)], limit=1)
            )
            if not operation:
                return Response("Location not found", status=404)
        else:
            operation = False

        # find exact match for desired occasions
        occasions = request.env["calendar.occasion"].sudo()
        no_occasions = int(appointment_length / BASE_DURATION)
        for i in range(no_occasions):
            domain = [
                ("start", "=", desired_time + timedelta(minutes=BASE_DURATION) * i),
                ("type_id", "=", type_id.id),
                ("appointment_id", "=", False),
            ]
            if operation:
                domain += [("operation_id", "=", operation.id), ("state", "=", "ok")]
            occasions |= request.env["calendar.occasion"].sudo().search(domain, limit=1)

        # reserve occasions if we found them
        if len(occasions) == no_occasions:
            app = request.env["calendar.occasion"].sudo().reserve_occasion(occasions)
            bookable_occasion_id = self.encode_bookable_occasion_id(occasions)
        else:
            app = False
            bookable_occasion_id = False

        if app:
            res = {
                "appointment_end_datetime": app.stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_start_datetime": app.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_length": int(app.duration * 60),
                "appointment_title": app.name or "",
                "appointment_type": app.type_id.ipf_num,
                "appointment_channel": app.channel.name or "",
                "customer_nr": app.partner_id.customer_id or "",
                "customer_name": app.partner_id.display_name or "",
                "employee_name": app.user_id.name or "",
                "employee_phone": app.user_id.phone or "",
                "employee_signature": app.user_id.name or "",
                "id": bookable_occasion_id,
                "appointment_id": app.id,
                "office_address": app.office_id.partner_id.contact_address or "",
                "office_email": app.office_id.partner_id.email or "",
                "location_code": app.operation_id.location_code or "",
                "office_code": app.office_id.office_code or "",
                "office_name": app.office_id.display_name or "",
                "status": app.state,
            }
            return res
        else:
            return Response("ID not found", status=404)

    @http.route(
        "/v1/appointments/bookable-occasions/reservation/<bookable_occasion_id>",
        type="http",
        csrf=False,
        auth="public",
        methods=["DELETE"],
    )
    def unreserve_bookable_occasion(self, bookable_occasion_id=False, **kwargs):
        # TODO: fix these error messages
        occasions = self.decode_bookable_occasion_id(bookable_occasion_id)
        if not occasions:
            return Response("ID not found", status=404)
        try:
            if request.env["calendar.appointment"].sudo().delete_reservation(occasions):
                return Response("OK, reservation deleted", status=200)
            else:
                return Response("ID not found", status=404)
        except:
            return Response("ID not found", status=404)

    @http.route(
        "/v1/appointments/appointments", type="http", auth="public", methods=["GET"]
    )
    def get_appointment(
        self,
        user_id=False,
        customer_nr=False,
        pnr=False,
        appointment_types=False,
        status_list=False,
        start=False,
        stop=False,
        **kwargs
    ):
        search_domain = []
        partner = False

        if not (
            user_id
            or customer_nr
            or pnr
            or appointment_types
            or status_list
            or start
            or stop
        ):
            return Response("No arguments given.", status=400)

        if pnr:
            partner = (
                request.env["res.partner"].sudo().search([("social_sec_nr", "=", pnr)])
            )
            if not partner:
                return Response("pnr. not found", status=404)
        elif customer_nr:
            pnr = request.env["af.ipf.endpoint"].sudo().get_pnr(customer_nr)
            if pnr:
                partner = (
                    request.env["res.partner"]
                    .sudo()
                    .search([("social_sec_nr", "=", pnr)])
                )
            if not partner:
                return Response("customer nr. not found", status=404)
        if user_id:
            user = request.env["res.users"].sudo().search([("login", "=", user_id)])
            if not user:
                return Response("user_id not found", status=404)
            user_domain = ("user_id", "=", user.id)
            search_domain.append(user_domain)

        if partner:
            partner_domain = ("partner_id", "=", partner.id)
            search_domain.append(partner_domain)

        if appointment_types:
            type_list = appointment_types.split(",")
            type_ids = (
                request.env["calendar.appointment.type"]
                .sudo()
                .search([("ipf_num", "in", type_list)])
                .mapped("id")
            )
            if (not type_ids) or (len(type_ids) != len(type_list)):
                return Response("Meeting type not found", status=404)
            type_ids_domain = ("type_id", "in", type_ids)
            search_domain.append(type_ids_domain)

        if status_list:
            status_list_list = status_list.split(",")
            status_list_domain = ("state", "in", status_list_list)
            search_domain.append(status_list_domain)

        if start:
            start_datetime = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
            start_datetime_domain = ("start", ">=", start_datetime)
            search_domain.append(start_datetime_domain)

        if stop:
            stop_datetime = datetime.strptime(stop, "%Y-%m-%dT%H:%M:%SZ")
            stop_datetime_domain = ("stop", "<=", stop_datetime)
            search_domain.append(stop_datetime_domain)

        apps = request.env["calendar.appointment"].sudo().search(search_domain)
        res = {"appointments": []}

        for app in apps:
            app_dict = {
                "appointment_end_datetime": app.stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_start_datetime": app.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_length": int(app.duration * 60),
                "appointment_title": app.name or "",
                "appointment_type": app.type_id.ipf_num,
                "appointment_channel": app.channel.name or "",
                "customer_nr": app.partner_id.customer_id or "",
                "customer_name": app.partner_id.display_name or "",
                "employee_name": app.user_id.name or "",
                "employee_phone": app.user_id.phone or "",
                "employee_signature": app.user_id.name or "",
                "id": app.id,
                "office_address": app.office_id.partner_id.contact_address or "",
                "office_email": app.office_id.partner_id.email or "",
                "location_code": app.operation_id.location_code or "",
                "office_code": app.office_id.office_code or "",
                "office_name": app.office_id.display_name or "",
                "status": app.state,
            }

            res["appointments"].append(app_dict)

        res = json.dumps(res)
        return Response(res, mimetype="application/json", status=200)

    @http.route(
        "/v1/appointments/appointments",
        type="json",
        csrf=False,
        auth="public",
        methods=["POST"],
    )
    def create_appointment(self, **kwargs):
        message = json.loads(request.httprequest.data)

        partner = False

        # hardcoding...
        sunie = (
            request.env["res.users"].sudo().search([("login", "=", "sunie")], limit=1)
        )
        sunie_office = (
            request.env["hr.department"]
            .sudo()
            .search([("office_code", "=", "0248")], limit=1)
        )

        bookable_occasion_id = message.get("bookable_occasion_id")
        customer_nr = message.get("customer_nr")
        pnr = message.get("pnr")

        if not customer_nr and not pnr:
            return Response("No customer nr. or pnr.", status=400)
        if pnr:
            partner = (
                request.env["res.partner"].sudo().search([("social_sec_nr", "=", pnr)])
            )
            if not partner:
                return Response("pnr. not found", status=404)
        elif customer_nr:
            pnr = request.env["af.ipf.endpoint"].sudo().get_pnr(customer_nr)
            if pnr:
                partner = (
                    request.env["res.partner"]
                    .sudo()
                    .search([("social_sec_nr", "=", pnr)])
                )
            if not partner:
                return Response("customer nr. not found", status=404)

        if not partner:
            return Response("Partner not found", status=404)

        if not bookable_occasion_id:
            return Response("No bookable_occasion_id.", status=400)

        occasions = self.decode_bookable_occasion_id(bookable_occasion_id)
        if not occasions:
            return Response("Bookable occasion id not found", status=404)
        if (
            occasions[0].appointment_id
            and occasions[0].appointment_id.state == "reserved"
        ):
            app = occasions[0].appointment_id
            app.partner_id = partner.id
            app._confirm_appointment()
        else:
            # check that occasions are free and unreserved
            free = True
            for occasion_id in occasions:
                if (
                    occasion_id.appointment_id
                    and occasion_id.appointment_id.state != "reserved"
                ) or (
                    occasion_id.appointment_id
                    and occasion_id.appointment_id.state == "reserved"
                    and occasion_id.appointment_id.reserved
                    > datetime.now() - timedelta(seconds=RESERVED_TIMEOUT)
                ):
                    free = False

            if not free:
                return Response("Bookable occasion id not free", status=403)

            vals = {
                "start": occasions[0].start,
                "stop": occasions[-1].stop,
                "duration": len(occasions) * BASE_DURATION / 60,
                "partner_id": partner.id,
                "state": "confirmed",
                "type_id": occasions[0].type_id.id,
                "channel": occasions[0].type_id.channel.id,
                "occasion_ids": [(6, 0, list(occasions.mapped("id")))],
                "name": occasions[0].type_id.name,
            }
            if occasions[0].user_id:
                vals["user_id"] = occasions[0].user_id
            if occasions[0].operation_id:
                vals["operation_id"] = occasions[0].operation_id
            app = request.env["calendar.appointment"].sudo().create(vals)

        if not app:
            return Response("Bad request", status=400)

        if app.type_id.channel == request.env.ref("calendar_channel.channel_local"):
            res = {
                "appointment_start_datetime": app.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_end_datetime": app.stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_length": int(app.duration * 60),
                "appointment_title": app.name or "",
                "appointment_type": app.type_id.ipf_num,
                "appointment_channel": app.type_id.channel.name or "",
                "customer_nr": app.partner_id.customer_id or "",
                "customer_name": app.partner_id.display_name or "",
                "employee_name": app.user_id.partner_id.name or "",
                "employee_phone": app.user_id.partner_id.phone or "",
                "employee_signature": app.user_id.login or "",
                "id": app.id,
                "office_address": app.office_id.partner_id.contact_address or "",
                "office_email": app.office_id.partner_id.email or "",
                "location_code": app.operation_id.location_code or "",
                "office_code": app.office_id.office_code or "",
                "office_name": app.office_id.display_name or "",
                "status": app.state,
            }
        else:
            res = {
                "appointment_start_datetime": app.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_end_datetime": app.stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "appointment_length": int(app.duration * 60),
                "appointment_title": app.name or "",
                "appointment_type": app.type_id.ipf_num,
                "appointment_channel": app.type_id.channel.name or "",
                "customer_nr": app.partner_id.customer_id or "",
                "customer_name": app.partner_id.display_name or "",
                "employee_name": sunie.partner_id.name or "",
                "employee_phone": sunie.partner_id.phone or "",
                "employee_signature": sunie.login or "",
                "id": app.id,
                "office_address": sunie_office.partner_id.contact_address or "",
                "office_email": sunie_office.partner_id.email or "",
                "location_code": app.operation_id.location_code or "",
                "office_code": sunie_office.office_code or "",
                "office_name": sunie_office.display_name or "",
                "status": app.state,
            }
        return res

    @http.route(
        "/v1/appointments/appointments/<appointment_id>",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def get_appointment_id(self, appointment_id=False, **kwargs):
        appointment_id = self.is_int(appointment_id)

        if appointment_id and appointment_id > 0:
            app = (
                request.env["calendar.appointment"]
                .sudo()
                .search([("id", "=", appointment_id)])
            )
            if app:
                res = {
                    "appointment_start_datetime": app.start.strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "appointment_end_datetime": app.stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "appointment_length": int(app.duration * 60),
                    "appointment_title": app.name or "",
                    "appointment_type": app.type_id.ipf_num,
                    "appointment_channel": app.type_id.channel.name or "",
                    "customer_nr": app.partner_id.customer_id or "",
                    "customer_name": app.partner_id.display_name or "",
                    "employee_name": app.user_id.partner_id.name or "",
                    "employee_phone": app.user_id.partner_id.phone or "",
                    "employee_signature": app.user_id.login or "",
                    "id": app.id or "",
                    "office_address": app.office_id.partner_id.contact_address or "",
                    "office_email": app.office_id.partner_id.email or "",
                    "location_code": app.operation_id.location_code or "",
                    "office_code": app.office_id.office_code or "",
                    "office_name": app.office_id.display_name or "",
                    "status": app.state,
                }

                # convert to json format
                res = json.dumps(res)
                return Response(res, mimetype="application/json", status=200)
            else:
                return Response("Bad request: id not found", status=404)
        else:
            return Response("Bad request: Invalid id", status=400)

    @http.route(
        "/v1/appointments/appointments/<appointment_id>",
        type="http",
        csrf=False,
        auth="public",
        methods=["DELETE"],
    )
    def delete_appointment(self, appointment_id, **kwargs):
        # _logger.warn('delete_appointment: args: %s' % appointment_id)

        appointment_id = self.is_int(appointment_id)

        if appointment_id and appointment_id > 0:
            appointment = (
                request.env["calendar.appointment"]
                .sudo()
                .search([("id", "=", appointment_id)])
            )
            if appointment:
                appointment.sudo().unlink()
                return Response("OK, deleted", status=200)
            else:
                return Response("ID not found", status=404)
        else:
            return Response("Bad request: Invalid id", status=400)

    @http.route(
        "/v1/appointments/appointments/<app_id>",
        type="json",
        auth="public",
        methods=["PUT"],
        csrf=False,
    )
    def update_appointment(self, app_id=False, **kwargs):
        message = json.loads(request.httprequest.data)

        bookable_occasion_id = message.get("bookable_occasion_id")
        # TODO: variables to be implemented:
        # title = message.get('title')
        # user_id = message.get('user_id')
        # customer_nr = message.get('customer_nr')
        # prn = message.get('prn')
        # appointment_type = message.get('appointment_type')
        # status = message.get('status')
        # start = message.get('start')
        # stop = message.get('stop')
        # duration = message.get('duration')
        # office = message.get('office')

        values = {}
        app = request.env["calendar.appointment"].sudo().search([("id", "=", app_id)])
        if app:
            if bookable_occasion_id:

                occasions = self.decode_bookable_occasion_id(bookable_occasion_id)
                if not occasions:
                    return Response("Bookable occasion id not found", status=404)

                # check that occasions are free and unreserved
                free = True
                for occasion_id in occasions:
                    if (
                        occasion_id.appointment_id
                        and occasion_id.appointment_id.state != "reserved"
                    ) or (
                        occasion_id.appointment_id
                        and occasion_id.appointment_id.state == "reserved"
                        and occasion_id.appointment_id.reserved
                        > datetime.now() - timedelta(seconds=RESERVED_TIMEOUT)
                    ):
                        free = False

                if not free:
                    return Response("Bookable occasion id not free", status=403)

                vals = {
                    "start": occasions[0].start,
                    "stop": occasions[-1].stop,
                    "duration": len(occasions) * BASE_DURATION / 60,
                    "occasion_ids": [(6, 0, list(occasions.mapped("id")))],
                    "name": occasions[0].type_id.name,
                }

                app.sudo().write(vals)

                res = {
                    "appointment_end_datetime": app.start.strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "appointment_start_datetime": app.stop.strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "appointment_length": int(app.duration * 60),
                    "appointment_title": app.name or "",
                    "appointment_type": app.type_id.ipf_num,
                    "appointment_channel": app.type_id.channel.name or "",
                    "customer_nr": app.partner_id.customer_id or "",
                    "customer_name": app.partner_id.display_name or "",
                    "employee_name": app.user_id.partner_id.name or "",
                    "employee_phone": app.user_id.partner_id.phone or "",
                    "employee_signature": app.user_id.login or "",
                    "id": app.id,
                    "office_address": app.office_id.partner_id.contact_address or "",
                    "office_email": app.office_id.partner_id.email or "",
                    "location_code": app.operation_id.location_code or "",
                    "office_code": app.office_id.office_code or "",
                    "office_name": app.office_id.display_name or "",
                    "status": app.state,
                }

                return res

            # TODO: Implement remaining features.
            # if title:
            #     values['title'] = title

            # if user_id:
            #     new_user = request.env['res.users'].sudo().search([('login', '=', user_id)])
            #     # values['user_id'] = [(5, 0, 0), (4, new_user.id, 0)]
            #     values['user_id'] = new_user.id

            # if customer_nr:
            #     new_customer = request.env['res.partner'].sudo().search([('customer_id', '=', customer_nr)])
            #     values['customer_nr'] = new_customer.customer_nr

            # if office:
            #     pass

            # if appointment_type:
            #     new_appointment_type = request.env['calendar.appointment.type'].sudo().search([('ipf_id', '=', appointment_type)])
            #     values['type_id'] = new_appointment_type.id

            # if values:
            #     app.sudo().write(values)
            # else:
            #     return Response("Bad request", status=400)
        else:
            return Response("Bad request: Invalid id", status=400)
