# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sellers_item_identification = fields.Char(string='Seller’s Item Identification')
    manufacturers_item_identification = fields.Char(string='Manufacturer’s Item Identification')
    item_specification_document_ref = fields.Char(string='Item Specification Document Reference')

    standard_item_identification_code = fields.Char(string='Standard Item Identification Code')
    standard_item_identification = fields.Char(string='Standard Item Identification')