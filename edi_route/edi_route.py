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
from odoo import models, fields, api, _
from pytz import timezone
import base64
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
import time
import dateutil
from time import strptime, mktime, strftime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval as eval
import sys
import traceback

import logging
_logger = logging.getLogger(__name__)

def html_line_breaks(msg):
    return msg.replace('\n', '<BR/>')

class edi_envelope(models.Model):
    _name = 'edi.envelope'
    _inherit = ['mail.thread']
    _description = 'EDI Envelope'

    name = fields.Char(string="Name",required=True)
    application = fields.Char('Application')
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
    date = fields.Datetime(string='Date',default=fields.Datetime.now())
    body = fields.Binary()
    edi_message_ids = fields.One2many(comodel_name='edi.message',inverse_name='envelope_id')
    state = fields.Selection([('progress', 'Progress'), ('sent','Sent'), ('received','Received'), ('canceled','Canceled')], default='progress')
    ref = fields.Char('Reference')
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

    @api.one
    def draft(self):
        self.state = 'progress'

    @api.one
    def split(self):
        try:
            if not self.state == "progress" or len(self.edi_message_ids)>0:
                raise TypeError('Cant split an already splited envelope')
            res = self._split()
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id and self.route_id.name,self.route_type,e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.envelope.split(): EDI ValueError Route %s type %s Error %s ' % (self.route_id and self.route_id.name,self.route_type,e))
            self.state = "canceled"
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id and self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = "canceled"
            _logger.error('edi.envelope.split(): EDI TypeError Route %s type %s Error %s ' % (self.route_id and self.route_id.name,self.route_type,e))
            #raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id and self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = "canceled"
            _logger.error('edi.envelope.split(): EDI IOError Route %s type %s Error %s ' % (self.route_id and self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        except Exception as e:
            self.env.cr.rollback()
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id and self.route_id.name or 'None', self.route_type or 'None', e)),
                    'subject': "Exception",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = "canceled"
            _logger.error('edi.envelope.split(): Exception %s type %s Error %s ' % (self.route_id and self.route_id.name or 'None', self.route_type, e))
        else:
            if self.state == 'progress':
                self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages created\n" % (self.route_id and self.route_id.name, ','.join(['%s(%s)' % (m.name, m.edi_type.name) for m in self.edi_message_ids]),'ok')),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
                self.state = "received"

    @api.one
    def _split(self):
        if self.route_type == 'plain':
            msg = self.env['edi.message'].create({
                'name': 'plain',
                'envelope_id': self.id,
                'body': self.body,
                'route_type': self.route_type,
                'sender': self.sender,
                'recipient': self.recipient,
                #~ 'consignor_id': sender.id,
                #~ 'consignee_id': recipient.id,
            })
            msg.unpack()
        self.envelope_opened()

    @api.one
    def envelope_opened(self):
        """Run when an envelope has been received and opened. Override to create control messages."""
        self.route_id.edi_action('edi.envelope.envelope_opened', envelope=self)

    @api.one
    def fold(self):
        #for m in self.env['edi.message'].search([('envelope_id','=',None),('route_id','=',route.id)]):
        #    m.envelope_id = self.id
        try:
            if not self.state == "progress" or self.body:
                raise TypeError('Cant fold an already folded envelope')
            res = self._fold(self.route_id)
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = "canceled"
            _logger.error('edi.envelope.fold(): EDI ValueError Route %s type %s #%s Error %s ' % (self.route_id.name,self.route_type,self.route_id.run_sequence,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s #%s Error %s\n" % (self.route_id.name,self.route_type,self.route_id.run_sequence,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = "canceled"
            _logger.error('edi.envelope.fold(): EDI TypeError Route %s type %s #%s Error %s ' % (self.route_id.name,self.route_type,self.route_id.run_sequence,e))
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error #%s %s\n" % (self.route_id.name,self.route_type,self.route_id.run_sequence,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = "canceled"
            _logger.error('edi.envelope.fold(): EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s #%s %s messages created\n" % (self.route_id.name,self.route_type,self.route_id.run_sequence,'ok')),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })

    @api.multi
    def _fold(self,route): # Folds messages in an envelope
        if route.route_type == 'plain':
            self.body = base64.b64encode(''.join([base64.b64decode(m.body) for m in self.edi_message_ids]))
        return self

class edi_message(models.Model):
    _name = 'edi.message'
    _inherit = ['mail.thread']
    _description = 'EDI Message'

    name = fields.Char(string="Name",required=True)
    envelope_id = fields.Many2one(comodel_name='edi.envelope', required=False)
    consignor_id = fields.Many2one(comodel_name='res.partner', required=False, string="Consignor", help="Consignor - the party sending the goods.")
    consignee_id = fields.Many2one(comodel_name='res.partner', required=False, string="Consignee", help="Consignee - the party receiving the goods.")
    sender = fields.Many2one(comodel_name='res.partner', string='Interchange Sender')
    recipient = fields.Many2one(comodel_name='res.partner', string='Interchange Recipient')
    forwarder_id = fields.Many2one(comodel_name='res.partner', string="Forwarder", help="Forwarder - the party planning the transport on behalf of the consignor or consignee.")
    carrier_id = fields.Many2one(comodel_name='res.partner', string="Carrier", help="Carrier - the party transporting the goods between two points.")
    body = fields.Binary()
    model = fields.Char(string="Model")
    res_id = fields.Integer()
    to_import = fields.Boolean(default=False)
    to_export = fields.Boolean(default=False)
    route_id = fields.Many2one(comodel_name="edi.route")
    route_type = fields.Selection(selection=[('plain','Plain')], default='plain')
    edi_type = fields.Many2one(comodel_name='edi.message.type', string="Edi Type")
    state = fields.Selection([('progress', 'Progress'), ('sent','Sent'), ('received','Received'), ('canceled','Canceled')], default='progress')
    
    def log(self, message, error_info=None, subject = ''):
        #TODO: Mail errors and implement this on envelope and message as well.
        if error_info:
            if type(error_info) == type([]):
                for e in error_info:
                    message += '\n' + ''.join(traceback.format_exception(e[0], e[1], e[2]))
            else:
                message += '\n' + ''.join(traceback.format_exception(error_info[0], error_info[1], error_info[2]))
        user = self.env['res.users'].browse(self._uid)
        self.env['mail.message'].create({
                'body': html_line_breaks(message),
                'subject': subject or '[%s] Debug EDI-message' % self.name,
                'author_id': user.partner_id.id,
                'res_id': self.id,
                'model': self._name,
                # 'type': 'notification',
            })
    
    @api.one
    def draft(self):
        self.state = 'progress'

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
                    # 'type': 'notification',
                })
            _logger.error('edi.message.unpack(): EDI ValueError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
            self.state = 'canceled'
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.message.unpack(): EDI TypeError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI TypeError in split %s' % e)
            self.state = 'canceled'
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.message.unpack(): EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
            self.state = 'canceled'
        except Warning as e:
            _logger.error('edi.message.unpack(): EDI Warning Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            self.state = 'canceled'
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages unpacked\n" % (self.route_id.name,self.route_type,self.edi_type.name)),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            self.state = 'received'

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
                    # 'type': 'notification',
                })
            _logger.error('edi.message.pack(): EDI ValueError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI ValueError in split %s (%s) %s' % (e,id,d))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Type Error %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.message.pack(): EDI TypeError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            raise
            raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s IOError %s\n" % (self.route_id.name,self.route_type,e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.message.pack(): EDI IOError Route %s type %s Error %s ' % (self.route_id.name,self.route_type,e))
            #raise Warning('EDI IOError in split %s' % e)
        else:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s %s messages packed\n" % (self.route_id.name, self.route_type, self.edi_type.name)),
                    'subject': "Success",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })

    @api.one
    def _pack(self):
        pass

    def _edi_message_create(self, edi_type=None, obj=None, sender=None, recipient=None, consignee=None, consignor=None, route=None, check_double=True):
        if consignee and obj and edi_type:
            #do not create message if edi type is not listed in consignee
            if not self.env.ref(edi_type).id in consignee.get_edi_types(consignee):
                return None
            if check_double and len(self.env['edi.message'].search([('model','=',obj._name),('res_id','=',obj.id),('edi_type','=',self.env.ref(edi_type).id)])) > 0:
                return None
            message = self.env['edi.message'].create({
                    'name': self.env.ref('edi_route.sequence_edi_message').next_by_id(),
                    'edi_type': self.env.ref(edi_type).id,
                    'model': obj._name,
                    'res_id': obj.id,
                    'route_id': route and route.id or self.env.ref('edi_route.main_route').id, #routes.get(edi_type,1),# self.env.ref('edi_route.main_route').id),
                    'route_type': route and route.route_type or self.env.ref('edi_route.main_route').route_type,
                    # This is a reply, switch recipient/sender unless we got excplicit parties
                    'sender': sender and sender.id or obj.unb_recipient.id,
                    'recipient': recipient and recipient.id or obj.unb_sender.id,
                    'consignor_id': consignor and consignor.id or self.env.ref('base.main_partner').id,
                    'consignee_id': consignee.id,
            })
            message.pack()
            self.env['mail.message'].create({
                    'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type=self.env.ref(edi_type).name,model=message._name,id=message.id,message=message.name),
                    'subject': self.env.ref(edi_type).name,
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': obj.id,
                    'model': obj._name,
                    # 'type': 'notification',
                })
            self.env['mail.message'].create({
                    'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type=self.env.ref(edi_type).name,model=obj._name,id=obj.id,message=obj.name),
                    'subject': self.env.ref(edi_type).name,
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': message.id,
                    'model': message._name,
                    # 'type': 'notification',
                })

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
    model_record = fields.Reference(string="Record", selection="_reference_models", compute="_model_record")

class edi_message_type(models.Model):
    _name = 'edi.message.type'
    _description = 'EDI Message Type'

    name = fields.Char(string="Name",required=True)

class edi_route(models.Model):
    _name = 'edi.route'
    _inherit = ['mail.thread']
    _description = 'EDI Route'

    name = fields.Char(string="Name",required=True)
    #partner_id = fields.Many2one(comodel_name='res.partner',required=True)
    active = fields.Boolean()
    protocol = fields.Selection(selection=[('none','None')])
    frequency_quant = fields.Integer(string="Frequency")
    frequency_uom = fields.Selection([('1','min'),('60','hour'),('1440','day'),('10080','week'),('40320','month')])
    next_run = fields.Datetime(string='Next run')
    run_sequence = fields.Char(string="Last run id")
    route_type = fields.Selection(selection=[('plain','Plain')],default='plain')
    test_mode = fields.Boolean('Test Mode') #TODO: Implement in BGM?
    route_line_ids = fields.One2many('edi.route.line', 'route_id', 'Python Acctions',copy=True)

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

    @api.multi
    def fold(self):
        """Folds messages in an envelope"""
        envelopes = []

        for route in self:
            messages = self.env['edi.message'].search([('envelope_id', '=', None), ('route_id', '=', route.id), ('body', '!=', None)])
            if len(messages) > 0:
                _logger.error('EDI Fold Route %s Messages %s ' % (route.name, messages))
                for recipient in set(messages.mapped(lambda msg: msg.recipient)):
                    _logger.error('EDI Fold Route %s type %s Recipient %s ' % (route.name, route.route_type, recipient))
                    #Sort by application
                    no_app_msg_ids = []
                    for app in recipient.edi_application_lines:
                        msg_ids = []
                        for msg in messages.filtered(lambda msg: msg.edi_type == app.edi_type and msg.recipient == recipient):
                            try:
                                msg.pack()
                                if app.name:
                                    msg_ids.append(msg.id)
                                else:
                                    no_app_msg_ids.append(msg.id)
                            except Exception as e:
                                _logger.warn("DAER: %s" % "Canceled envelope at edi_route")
                                msg.state = 'canceled'
                        if app.name and msg_ids:
                            envelope = self.env['edi.envelope'].create({
                                # 'name': self.env['ir.sequence'].next_by_id(self.env.ref('edi_route.sequence_edi_envelope').id),
                                'name': self.env.ref('edi_route.sequence_edi_envelope').next_by_id(),
                                'route_id': route.id,
                                'route_type': route.route_type,
                                'recipient': recipient.id,
                                'sender': self.env.ref('base.main_partner').id,
                                'application': app.name,
                                'edi_message_ids': [(6, 0, msg_ids)]
                            })
                            envelope.fold()
                            envelopes.append(envelope)
                    #Handle all messages not covered by named applications
                    if no_app_msg_ids:
                        envelope = self.env['edi.envelope'].create({
                            'name': self.env.ref('edi_route.sequence_edi_envelope').next_by_id(),
                            'route_id': route.id,
                            'route_type': route.route_type,
                            'recipient': recipient.id,
                            'sender': self.env.ref('base.main_partner').id,
                            'edi_message_ids': [(6, 0, no_app_msg_ids)]
                        })
                        envelope.fold()
                        envelopes.append(envelope)
        return envelopes

    @api.multi
    def _run_out(self, envelopes):
        pass

    @api.multi
    def _run_in(self):
        return []

    @api.one
    def run(self):
        # out
        run_performed = False
        try:
            # create outgoing envelopes
            envelopes = self.fold()
            for e in self.env['edi.envelope'].search([('state', '=', 'progress'), ('route_id', '=', self.id)]):
                if e not in envelopes:
                    envelopes.append(e)
            self._run_out(envelopes)
            if envelopes:
                run_performed = True
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Value Error %s\n" % (self.name, self.route_type, e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.route.run() (out): EDI ValueError Route %s type %s Error %s ' % (self.name, self.route_type, e))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Type Error %s\n" % (self.name, self.route_type, e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.route.run() (out): EDI TypeError Route %s type %s Error %s ' % (self.name, self.route_type, e))
            raise Warning('EDI TypeError in run(out) %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s IOError %s\n" % (self.name, self.route_type, e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.route.run() (out): EDI IOError Route %s type %s Error %s ' % (self.name, self.route_type, e))
        else:
            #~ self.env['mail.message'].create({
                    #~ 'body': _("Route %s type %s %s messages created\n" % (self.name, self.route_type, 'ok')),
                    #~ 'subject': "Success",
                    #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    #~ 'res_id': self.id,
                    #~ 'model': self._name,
                    #~ 'type': 'notification',})
            pass

        # in
        try:
            envelopes = self._run_in()
        except ValueError as e:
            id = self.env['mail.message'].create({
                    'body': _("Route %s type %s Value Error %s\n" % (self.name, self.route_type, e)),
                    'subject': "ValueError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.route.run() (in): EDI ValueError Route %s type %s Error %s ' % (self.name, self.route_type, e))
        except TypeError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s Type Error %s\n" % (self.name, self.route_type, e)),
                    'subject': "TypeError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.route.run() (in): EDI TypeError Route %s type %s Error %s ' % (self.name, self.route_type, e))
            raise Warning('EDI TypeError in split %s' % e)
        except IOError as e:
            self.env['mail.message'].create({
                    'body': _("Route %s type %s IOError %s\n" % (self.name, self.route_type, e)),
                    'subject': "IOError",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            _logger.error('edi.route.run() (in): EDI IOError Route %s type %s Error %s ' % (self.name, self.route_type, e))
        else:
            #~ self.env['mail.message'].create({
                    #~ 'body': _("Route %s type %s %s messages created\n" % (self.name, self.route_type, 'ok')),
                    #~ 'subject': "Success",
                    #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    #~ 'res_id': self.id,
                    #~ 'model': self._name,
                    #~ 'type': 'notification',})
            pass
        finally:
            if envelopes:
                run_performed = True
                for envelope in envelopes:
                    if envelope.state == 'progress':
                        try:
                            self._cr.commit()
                            envelope.split()
                        except Exception as e:
                            self._cr.rollback()
                            envelope.state = 'canceled'
                            #TODO: Handle Warning
                            self.log('Error when processing envelope %s\n%s' % (envelope.name, e))
        if run_performed:
            self.run_sequence = self.env.ref('edi_route.sequence_edi_run').next_by_id()
    
    def log(self, message, error_info=None):
        #TODO: Mail errors and implement this on envelope and message as well.
        if error_info:
            if type(error_info) == type([]):
                for e in error_info:
                    message += '\n' + ''.join(traceback.format_exception(e[0], e[1], e[2]))
            else:
                message += '\n' + ''.join(traceback.format_exception(error_info[0], error_info[1], error_info[2]))
        user = self.env['res.users'].browse(self._uid)
        self.env['mail.message'].create({
                'body': html_line_breaks(message),
                'subject': '[%s] Debug EDI-route' % self.run_sequence,
                'author_id': user.partner_id.id,
                'res_id': self.id,
                'model': self._name,
                # 'type': 'notification',
            })
    
    # @api.v7
    # def cron_job(self, cr, uid, context=None):
    #     for route in self.pool.get('edi.route').browse(cr, uid, self.pool.get('edi.route').search(cr, uid, [('active','=',True)])):
    #         if not route.next_run:
    #             route.next_run = fields.Datetime.now()
    #         if (route.next_run < fields.Datetime.now()):
    #             route.run()
    #             route.next_run = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(minutes=route.frequency_quant * int(route.frequency_uom))
    #             _logger.info('Cron job for %s done' % route.name)

    @api.one
    def cron_job(self):
        for route in self.pool.get('edi.route').browse(self.pool.get('edi.route').search([('active','=',True)])):
            if not route.next_run:
                route.next_run = fields.Datetime.now()
            if (route.next_run < fields.Datetime.now()):
                route.run()
                route.next_run = fields.Datetime.from_string(fields.Datetime.now()) + timedelta(minutes=route.frequency_quant * int(route.frequency_uom))
                _logger.info('Cron job for %s done' % route.name)

    @api.one
    def edi_action(self, caller_name, **kwargs):
        _logger.debug("Caller ID: %s kwargs %s" % (caller_name, kwargs))
        caller = self.env['edi.route.caller'].search([('name', '=', caller_name)], limit=1)
        if caller:
            _logger.debug("Caller: %s; %s" % (caller.name, self.route_line_ids.filtered(lambda a: a.caller_id.id == caller.id)))
            for action in self.route_line_ids.filtered(lambda a: a.caller_id.id == caller.id):
                _logger.debug("Caller ID: %s; line %s kwargs %s" % (caller_name, action.name,kwargs))
                action.run_action_code(kwargs)
        else:
            #raise Warning(caller_name,kwargs)
            self.env['mail.message'].create({
                    'body': _("Caller ID not found: %s; kwargs %s" % (caller_name, kwargs)),
                    'subject': "EDI Error %s" % caller_name,
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    # 'type': 'notification',
                })
            obj = kwargs.get('order') or kwargs.get('picking') or kwargs.get('invoice')
            if obj:
                self.env['mail.message'].create({
                        'body': _("Caller ID not found: %s; kwargs %s" % (caller_name, kwargs)),
                        'subject': "EDI Error %s" % caller_name,
                        'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                        'res_id': obj.id,
                        'model': obj._name,
                        # 'type': 'notification',
                    })
            _logger.error("Caller ID not found: %s; kwargs %s" % (caller_name, kwargs))

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
        try:
            eval_context = self._get_eval_context(values)
            eval(self.code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'result'
            if 'result' in eval_context:
                return eval_context['result']
        except SyntaxError:
            _logger.error('code %s values %s' %(self.code.strip(), self._get_eval_context(values)))

    @api.multi
    def _get_eval_context(self, values):
        """ Prepare the context used when evaluating python code.

        :returns: dict -- evaluation context given to (safe_)eval """
        import odoo
        values.update({
            # python libs
            'time': time,
            'datetime': datetime,
            'dateutil': dateutil,
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
    _description = 'EDI Route Caller'

    name = fields.Char('name')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Caller ID must be unique!'),
    ]

class edi_application_line(models.Model):
    _name = 'edi.application.line'
    _description = 'EDI Application Line'

    name = fields.Char('Application Reference',help="Used sometimes in envelop as Interchange Control Ref")
    edi_type = fields.Many2one('edi.message.type', required=True)
    partner_id = fields.Many2one('res.partner', required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
