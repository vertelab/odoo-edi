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
import base64
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
    #partner_id = fields.Many2one(string="Partner",related='route_id.partner_id',readonly=True)
    direction = fields.Selection(related="route_id.direction",readonly=True)
    date = fields.Datetime(string='Date',default=fields.Datetime.now())
    body = fields.Binary()
    message_ids = fields.One2many(comodel_name='edi.message',inverse_name='envelope_id')
    state = fields.Selection([('progress','Progress'),('sent','Sent'),('recieved','Receieved'),('canceled','Canceled')],default='progress')
    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('envelope_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
    def _envelope_type(self):
        return [('plain','Plain')]
    envelope_type = fields.Selection(selection='_envelope_type',default='plain')

    
    #~ @api.one
    #~ def transform(self):
        #~ pass
    
    @api.one
    def split(self):
        pass
                
    @api.one
    def fold(self,route): # Folds messages in an envelope
        if route.envelope_type == 'plain':
            self.body = base64.b64encode(''.join([base64.b64decode(m.body) for m in self.message_ids]))
        return self
                    
    def _cron_job_in(self,cr,uid, edi, context=None):
        edi.write({'to_import': False})

    def _cron_job_out(self,cr,uid, edi, context=None):
        edi.write({'to_export': False})
    
    @api.v7
    def cron_job(self, cr, uid, context=None):
        for edi in self.pool.get('edi.message').browse(cr, uid, self.pool.get('edi.message').search(cr, uid, [('to_export','=',True)])):
            edi._cron_job_out(cr,uid,edi,context=context)

class edi_message(models.Model):
    _name = 'edi.message' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name",required=True)
    envelope_id = fields.Many2one(comodel_name='edi.envelope',required=False)
    consignor_id = fields.Many2one(comodel_name='res.partner',required=False,string="Consignor",help="Consignor - the party sending the goods.") 
    consignee_id = fields.Many2one(comodel_name='res.partner',required=False,string="Consignee",help="Consignee - the party receiving the goods.") 
    forwarder_id = fields.Many2one(comodel_name='res.partner',string="Forwarder",help="Forwarder - the party planning the transport on behalf of the consignor or consignee.") 
    carrier_id = fields.Many2one(comodel_name='res.partner',string="Carrier",help="Carrier - the party transporting the goods between two points.") 
    body = fields.Binary()
    model = fields.Char(string="Model")
    res_id = fields.Integer()
    to_import = fields.Boolean(default=False)
    to_export = fields.Boolean(default=False)
    route_id = fields.Many2one(comodel_name="edi.route")
    edi_type = fields.Selection(selection=[('none','None')],default='none')

    @api.one
    def unpack(self):
        pass
    
    @api.one
    def pack(self):
        #~ if not self.model_record:
            #~ raise Warning("ORDRSP: Can not create message without attached sale.order record!")
        self.name = self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_message').id)
    
    def _cron_job_in(self,cr,uid, edi, context=None):
        edi.write({'to_import': False})

    def _cron_job_out(self,cr,uid, edi, context=None):
        edi.write({'to_export': False})

    def _edi_message_create(self, edi_type=None,obj=None, partner=None, check_route=True, check_double=True):
        if partner and obj and edi_type:
            routes = partner.get_routes(partner)
            if check_route and not edi_type in routes:
                return None
            if check_double and len(self.env['edi.message'].search([('model','=',obj._name),('res_id','=',obj.id),('edi_type','=',edi_type)])) > 0:
                return None
            message = self.env['edi.message'].create({
                    'name': self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_message').id),
                    'edi_type': edi_type,
                    'model': obj._name,
                    'res_id': obj.id,
                    'route_id': routes.get(edi_type,1),
                    'consignor_id': self.env.ref('base.main_partner').id,
                    'consignee_id': partner.id,
            })
            message.pack()
            self.env['mail.message'].create({
                    'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type=edi_type,model=message._name,id=message.id,message=message.name),
                    'subject': edi_type,
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': obj.id,
                    'model': obj._name,
                    'type': 'notification',})                
            self.env['mail.message'].create({
                    'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type=edi_type,model=obj._name,id=obj.id,message=obj.name),
                    'subject': edi_type,
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': message.id,
                    'model': message._name,
                    'type': 'notification',})                

    @api.v7
    def cron_job(self, cr, uid, context=None):
        for edi in self.pool.get('edi.message').browse(cr, uid, self.pool.get('edi.message').search(cr, uid, [('to_import','=',True)])):
            edi._cron_job_in(cr,uid,edi,context=context)
        for edi in self.pool.get('edi.message').browse(cr, uid, self.pool.get('edi.message').search(cr, uid, [('to_export','=',True)])):
            edi._cron_job_out(cr,uid,edi,context=context)
    
    @api.one
    def _model_record(self):
        if self.model and self.res_id and self.env[self.model].browse(self.res_id):
            self.model_record = self.env[self.model].browse(self.res_id)

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([('state', '!=', 'manual')])
#        return self.env[self.model].browse(self.res_id)
        return [(model.model, model.name)
                for model in models
                if not model.model.startswith('ir.')]
    model_record = fields.Reference(string="Record",selection="_reference_models",compute="_model_record")
    
class edi_route(models.Model):
    _name = 'edi.route' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name",required=True)
    partner_id = fields.Many2one(comodel_name='res.partner',required=True)
    active = fields.Boolean()
    route_type = fields.Selection(selection=[('none','None')])
    direction = fields.Selection([('in','In'),('out','Out')])
    frequency_quant = fields.Integer(string="Frequency")
    frequency_uom = fields.Selection([('1','min'),('60','hour'),('1440','day'),('10080','week'),('40320','month')])
    next_run = fields.Datetime(string='Next run')
    run_sequence = fields.Char(string="Last run id")
    edi_type = fields.Selection(selection=[('none','None')],default='none')
    envelope_type = fields.Selection(selection=[('plain','Plain')],default='plain')
    test_mode = fields.Boolean('Test Mode') #TODO: Implement in BGM?
    
    @api.one
    def _envelope_count(self):
        self.envelope_count = len(self.env['edi.envelope'].search([('route_id','=',self.id)]))
        self.envelope_count = 42
        self.envelope_count = self.env['edi.envelope'].search_count([('route_id','=',self.id)])
    envelope_count = fields.Integer(compute='_envelope_count',string="# envelopes")
    @api.one
    def _message_count(self):
        self.message_count = len(self.env['edi.message'].search([('route_id','=',self.id)]))
        self.message_count = self.env['edi.message'].search_count([('route_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
    
    @api.one
    def check_connection(self):
        _logger.info('Check connection [%s:%s]' % (self.name,self.route_type))
        
    @api.one
    def fold(self): # Folds messages in an envelope
        envelope = self.env['edi.envelope'].create({
            'name': self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_envelope').id),
            'route_id': self.id,
            })
        for m in self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',self.id)]):
            m.envelope_id = envelope.id
        envelope.fold(self)
        return envelope
        
    @api.one
    def put_file(self,file):
        pass
        
    @api.one
    def run(self):
        self.run_sequence = self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_run').id)
      
        
    def log(self,message):
        user = self.env['res.users'].browse(self._uid)  
        self.env['mail.message'].create({
                'body': message,
                'subject': '[%s] Debug EDI-route' % self.run_sequence,
                'author_id': user.partner_id.id,
                'res_id': self.id,
                'model': self._name,
                'type': 'notification',})                
    
    @api.v7
    def cron_job(self, cr, uid, context=None):
        for route in self.pool.get('edi.route').browse(cr, uid, self.pool.get('edi.route').search(cr, uid, [('active','=',True)])):
            if (datetime.fromtimestamp(mktime(strptime(route.next_run, DEFAULT_SERVER_DATETIME_FORMAT))) < datetime.today()):
                route.run()
                route.next_run = datetime.fromtimestamp(mktime(strptime(route.next_run, DEFAULT_SERVER_DATETIME_FORMAT))) + timedelta(minutes=route.frequency_quant * int(route.frequency_uom))
                _logger.info('Cron job for %s done' % route.name)

class res_partner(models.Model):
    _inherit='res.partner'
    
    gln = fields.Char(string="Global Location Number",help="Global Location Number (GLN)")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
