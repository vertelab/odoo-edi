# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiTransport(models.Model):
    _name = 'edi.transport'
    _description = 'Edi Transport'

    name = fields.Char(name="Name")
    