# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _
from pytz import timezone
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta, time
from time import strptime, mktime, strftime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


import logging
_logger = logging.getLogger(__name__)

            
class edi_envelope(models.Model):
    _name = 'edi.envelope' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name",required=True)
    route_id = fields.Many2one(comodel_name='edi.route',required=True)
    partner_id = fields.Many2one(string="Partner",related='route_id.partner_id.id')
    edi_type = fields.Selection(related="route_id.edi_type")
    direction = fields.Selection(related="route_id.direction")
    date = fields.DateTime(string='Date')
    body = fields.Binary()
    message_ids = fields.One2many(comodel_name='edi.message',inverse_name='envelope_id')
    state = fields.Selection([('progress','Progress'),('sent','Sent'),('recieved','Receieved'),('canceled','Canceled')])
    
    @api.one
    def transform(self):
        pass
        
        
class edi_message(models.Model):
    _name = 'edi.message' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name",required=True)
    envelope_id = fields.Many2one(comodel_name='edi.envelope',required=True)
    edi_type = fields.Selection(related="envelope_id.edi_type")
    body = fields.Binary()
    model = fields.Many2one(comodel_name="ir.model")
    res_id = fields.Integer()
    
class edi_route(models.Model):
    _name = 'edi.route' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name",required=True)
    partner_id = fields.Many2one(comodel_name='res.partner',required=True)
    active = fields.Boolean()
    def _route_type(self):
        return [('none','None')]
    route_type = fields.Selection(selection='_route_type')
    def _edi_type(self):
        return [('none','None')]
    edi_type = fields.Selection(selection='_edi_type')
    direction = fields.Selection([('in','In'),('out','Out')])
    frequency_quant = fields.Integer(string="Frequency")
    frequency_uom = fields.Selection([('1','min'),('60','hour'),('1440','day'),('10080','week'),('40320','month')])
    next_run = fields.DateTime(string='Next run')
    model = fields.Many2one(comodel_name="ir.model")
    
    @api.one
    def check_connection(self):
        _logger.info('Check connection [%s:%s]' % (self.name,self.route_type))
        
   @api.one
    def get_file(self):
        pass
        
    @api.one
    def put_file(self,file):
        pass
        
    @api.one
    def run(self):
        pass

    @api.v7
    def cron_job(self, cr, uid, context=None):
        for route in self.pool.get('edi.route').browse(cr, uid, self.pool.get('edi.route').search(cr, uid, [('active','=',True)])):
            if (datetime.fromtimestamp(mktime(strptime(route.next_run, DEFAULT_SERVER_DATETIME_FORMAT))) < datetime.today()):
                route.run()
                route.next_run = datetime.fromtimestamp(mktime(strptime(route.next_run, DEFAULT_SERVER_DATETIME_FORMAT))) + timedelta(minutes=route.frequency_quant * int(route.frequency_uom))
                _logger.info('Cron job for %s done' % route.name)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
