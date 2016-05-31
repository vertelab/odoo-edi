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
from openerp.tools.safe_eval import safe_eval as eval

import logging
_logger = logging.getLogger(__name__)

            
class edi_envelope(models.Model):
    _name = 'edi.envelope' 
    _inherit = ['mail.thread']
    
    name = fields.Char(string="Name",required=True)
    sender = fields.Many2one(comodel_name='res.partner', string='Interchange Sender')
    recipient = fields.Many2one(comodel_name='res.partner', string='Interchange Recipient')
    @api.model
    def _route_default(self):
        route = self.env['edi.route'].browse(self._context.get('default_route_id'))
        if route:
            return route.id
        else:
            return self.env['edi.route'].search([])[0]
    route_id = fields.Many2one(comodel_name='edi.route',required=True,default=_route_default)
    #partner_id = fields.Many2one(string="Partner",related='route_id.partner_id',readonly=True)
    date = fields.Datetime(string='Date',default=fields.Datetime.now())
    body = fields.Binary()
    edi_message_ids = fields.One2many(comodel_name='edi.message',inverse_name='envelope_id')
    state = fields.Selection([('progress','Progress'),('sent','Sent'),('recieved','Recieved'),('canceled','Canceled')],default='progress')
    @api.one
    def _message_count(self):
        self.message_count = self.env['edi.message'].search_count([('envelope_id','=',self.id)])
    message_count = fields.Integer(compute='_message_count',string="# messages")
    #change to related field?
    
    @api.model
    def _route_type_default(self):
        route = self.env['edi.route'].browse(self._context.get('default_route_id'))
        if route:
            return route.route_type
        else:
            'plain'
    route_type = fields.Selection(selection=[('plain','Plain')],default=_route_type_default)
    

    
    #~ @api.one
    #~ def transform(self):
        #~ pass
    
    @api.one
    def split(self):
        try:
            res = self._split()
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})  
            _logger.error('EDI ValueError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI TypeError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages crceated\n" % (self.route_id.name,self.route_type,'ok')), #len(self.edi_messages_ids))),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            
        #~ finally:
            #~ pass
        

    @api.one
    def _split(self):
        if self.route_type == 'plain':
            msg = self.env['edi.message'].create({
                'name': 'plain',
                'envelope_id': self.id,
                'body': self.body,
                'edi_type': 'none',
                #~ 'consignor_id': sender.id,
                #~ 'consignee_id': recipient.id,
            })
            msg.unpack()

    @api.one
    def fold(self):
        #for m in self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',route.id)]):
        #    m.envelope_id = self.id
        try:
            res = self._fold(self.route_id)
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})  
            _logger.error('EDI ValueError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI TypeError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            raise
            #raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages crceated\n" % (self.route_id.name,self.route_type,'ok')), #len(self.edi_messages_ids))),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})

                                
    @api.multi
    def _fold(self,route): # Folds messages in an envelope
        if route.route_type == 'plain':
            self.body = base64.b64encode(''.join([base64.b64decode(m.body) for m in self.edi_message_ids]))
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
    sender = fields.Many2one(comodel_name='res.partner', string='Interchange Sender')
    recipient = fields.Many2one(comodel_name='res.partner', string='Interchange Recipient')
    forwarder_id = fields.Many2one(comodel_name='res.partner',string="Forwarder",help="Forwarder - the party planning the transport on behalf of the consignor or consignee.") 
    carrier_id = fields.Many2one(comodel_name='res.partner',string="Carrier",help="Carrier - the party transporting the goods between two points.") 
    body = fields.Binary()
    model = fields.Char(string="Model")
    res_id = fields.Integer()
    to_import = fields.Boolean(default=False)
    to_export = fields.Boolean(default=False)
    route_id = fields.Many2one(comodel_name="edi.route")
    route_type = fields.Selection(selection=[('plain','Plain')],default='plain')
    edi_type = fields.Selection(selection=[('none','None')],default='none')
    
    @api.one
    def unpack(self):
        try:
            res = self._unpack()
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})  
            _logger.error('EDI ValueError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI TypeError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages crceated\n" % (self.route_id.name,self.route_type,'ok')), #len(self.edi_messages_ids))),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
        #~ finally:
            #~ pass
        

    @api.one
    def _unpack(self):
        pass

    @api.one
    def pack(self):
        try:
            res = self._pack()
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Value Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})  
            _logger.error('EDI ValueError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Type Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI TypeError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            raise
            raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s IOError %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
            _logger.error('EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages crceated\n" % (self.route_id.name,self.route_type,'ok')), #len(self.edi_messages_ids))),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
        #~ finally:
            #~ pass


    @api.one
    def _pack(self):
        pass
    
    def _cron_job_in(self,cr,uid, edi, context=None):
        edi.write({'to_import': False})

    def _cron_job_out(self,cr,uid, edi, context=None):
        edi.write({'to_export': False})

    def _edi_message_create(self, edi_type=None,obj=None, partner=None, route=None, check_double=True):
        if partner and obj and edi_type:
            if check_double and len(self.env['edi.message'].search([('model','=',obj._name),('res_id','=',obj.id),('edi_type','=',edi_type)])) > 0:
                return None
            message = self.env['edi.message'].create({
                    'name': self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_message').id),
                    'edi_type': edi_type,
                    'model': obj._name,
                    'res_id': obj.id,
                    'route_id': route and route.id or self.env.ref('edi_route.main_route').id, #routes.get(edi_type,1),# self.env.ref('edi_route.main_route').id),
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
    protocol = fields.Selection(selection=[('none','None')])
    frequency_quant = fields.Integer(string="Frequency")
    frequency_uom = fields.Selection([('1','min'),('60','hour'),('1440','day'),('10080','week'),('40320','month')])
    next_run = fields.Datetime(string='Next run')
    run_sequence = fields.Char(string="Last run id")
    route_type = fields.Selection(selection=[('plain','Plain')],default='plain')
    test_mode = fields.Boolean('Test Mode') #TODO: Implement in BGM?
    route_line_ids = fields.One2many('edi.route.line', 'route_id', 'Python Acctions')
    
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
        messages = self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',self.id)])
        if len(messages)>0:
            for recipient in set(messages.mapped(lambda msg: msg.recipient)):
                envelope = self.env['edi.envelope'].create({
                        'name': self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_envelope').id),
                        'route_id': self.id,
                        'route_type': self.route_type,
                        'recipient': recipient.id,
                        'sender': self.env.ref('base.main_partner').id,
                        })
                for msg in messages.filtered(lambda msg: msg.recipient == recipient):
                    m.pack()
                    m.envelope_id = envelope.id
                envelope.fold()

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
    
    @api.one
    def edi_action(self, caller_name, **kwargs):
        caller = self.env['edi.route.caller'].search([('name', '=', caller_name)])
        if caller:
            for action in self.env['edi.route.line'].search([('caller_id', '=', caller.id), ('route_id', '=', self.id)]):
                _logger.info("Caller ID: %s; line %s kwargs %s" % (caller_name, action.name,kwargs))
                action.run_action_code(kwargs)
        else:
            _logger.info("Caller ID: %s; no matching line kwargs %s" % (caller_name, kwargs))

class edi_route_lines(models.Model):
    _name = 'edi.route.line'
    
    name = fields.Char('name')
    caller_id = fields.Many2one('edi.route.caller','Caller ID', help="Unique ID representing the method that should trigger this action, eg. 'sale.order.action_invoice_create'.", required=True)
    code = fields.Text('Python Action', required=True, default="""#
#env - Environment
#Warning - Warning
#invoice._edi_message_create('INVOIC',check_double=True)
#
"""
    )
    route_id = fields.Many2one('edi.route', 'EDI Route', required=True)
    
    @api.one
    def run_action_code(self, values):
        eval_context = self._get_eval_context(values)
        eval(self.code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'result'
        if 'result' in eval_context:
            return eval_context['result']
    
    @api.multi
    def _get_eval_context(self, values):
        """ Prepare the context used when evaluating python code.

        :returns: dict -- evaluation context given to (safe_)eval """
        import openerp
        values.update({
            # python libs
            #~ 'time': time,
            #~ 'datetime': datetime,
            #~ 'dateutil': dateutil,
            #~ # NOTE: only `timezone` function. Do not provide the whole `pytz` module as users
            #~ #       will have access to `pytz.os` and `pytz.sys` to do nasty things...
            #~ 'timezone': pytz.timezone,
            # orm
            'env': self.env,
            # Exceptions
            'Warning': openerp.exceptions.Warning,
        })
        return values
        
class edi_route_caller(models.Model):
    _name = 'edi.route.caller'
    
    name = fields.Char('name')
   

class res_partner(models.Model):
    _inherit='res.partner'
    
    gln = fields.Char(string="Global Location Number",help="Global Location Number (GLN)")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
