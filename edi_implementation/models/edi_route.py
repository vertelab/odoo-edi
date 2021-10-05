# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
from odoo.addons.edi_base.models.edi_error import EDIUnkownMessageError
from urllib import request
from urllib.error import HTTPError, URLError
import json
import ssl
import uuid

_logger = logging.getLogger(__name__)


class EdiRouteRest(models.Model):
    _inherit = "edi.route"
