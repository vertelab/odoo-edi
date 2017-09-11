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
from openerp.exceptions import except_orm, Warning, RedirectWarning


import time
import datetime
import fnmatch
import zipfile
import base64

import re

import logging
_logger = logging.getLogger(__name__)

class edi_envelope(models.Model):
    _inherit = 'edi.envelope'

    mail_id = fields.Many2one(comodel_name="mail.message")
    route_type = fields.Selection(selection_add=[('mail','Mail')])
    
    
    def _check_mail_attachments(self):
        for attachment in self.mail_id.attachment_ids:
            if attachment.mimetype == 'application/pdf':
                pass # attachment.pdf2image(800,1200)
            elif attachment.mimetype in ['image/jpeg','image/png','image/gif']:
                pass
    def _check_mail_pattern(self):
        txt = self.mail_id.subject + self.mail_id.body
        for attachment in self.mail_id.attachment_ids:
            txt += attachment.index_content
        m = re.search(self.pattern,txt)
        return m.group(0)
    

    @api.one
    def split(self):
        self.mail_id = self.env['mail.message'].search([('model','=','edi.envelope'),('res_id','=',self.id),('type','=','email')])
        self.sender = self.mail_id.author_id
        self._check_mail_attachments()  # 
        key = self._check_mail_pattern()

        record = self.env[self.model_id.name].search(['|',('name','=',key),('reference_type','=',key)])
        if record:
            for attachment in self.mail_id.attachment_ids:
                attachment.res_model = record._name
                attachment.res_id = record.id
        
        super(edi_envelope,self).split()

#~ class edi_message(models.Model):
    #~ _inherit='edi.message'
    #~ route_type = fields.Selection(selection_add=[('mail','Mail')])
    
    #~ @api.one
    #~ def unpack(self):
        #~ _logger.warning('unpack (edi_route_mail) %s %s' % (self.edi_type.name, self))
        #~ if self.edi_type.id == self.env.ref('edi_route_mail.edi_message_type_invoice_pdf'):
            #~ invoice = self.env['account.invoice'].create({
                #~ 'name': self.envelope_id.mail_id.subject,
                #~ 'origin': _('mail'),
                #~ 'type': 'in_invoice',
                #~ 'reference': self.envelope_id.mail_id.subject,
                #~ 'account_id': self.consignor_id.property_account_receivable.id,
                #~ 'partner_id': self.consignor_id.id,
                #~ 'journal_id': self.env['account.invoice'].default_get(['journal_id'])['journal_id'],
                #~ 'currency_id': self.consignor_id.property_product_pricelist and self.consignor_id.property_product_pricelist.currency_id.id or False,
                #~ 'comment': self.envelope_id.mail_id.body,
                #~ 'payment_term': self.consignor_id.property_payment_term and self.consignor_id.property_payment_term.id or False,
                #~ 'fiscal_position': self.consignor_id.property_account_position and self.consignor_id.property_account_position.id or False,
                #~ 'date_invoice': self.envelope_id.mail_id.date,
                #~ 'company_id': self.env['res.users']._get_company(),
                #~ 'user_id': self.consignor_id.user_id and self.consignor_id.user_id.id or self.env.uid,
            #~ })
            #~ self.write({'model': 'account.invoice', 'res_id': invoice.id})
            #~ self.env['mail.message'].create({
                    #~ 'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type=self.edi_type.name,model=self._name,id=self.id,message=self.name),
                    #~ 'subject': self.edi_type.name,
                    #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    #~ 'res_id': invoice.id,
                    #~ 'model': invoice._name,
                    #~ 'type': 'notification',})
            #~ self.env['mail.message'].create({
                    #~ 'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type='invoice_pdf',model=invoice._name,id=invoice.id,message=invoice.name),
                    #~ 'subject': self.edi_type.name,
                    #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    #~ 'res_id': self.id,
                    #~ 'model': self._name,
                    #~ 'type': 'notification',})

        #~ else:
            #~ super(edi_message, self).unpack()


class edi_route(models.Model):
    _inherit = 'edi.route'
    _inherits = {"mail.alias": "alias_id"}

    alias_id = fields.Many2one(comodel_name='mail.alias', string='Alias', ondelete="restrict", required=True,
                                    help="Internal email associated with this route. Incoming emails are automatically synchronized"
                                         "with messagesd.")
    alias_model = fields.Char(String="Alias Model",default='edi.envelope')
    mail_debug = fields.Boolean(string="Debug",required=False)
    protocol = fields.Selection(selection_add=[('mail','Mail')])
    route_type = fields.Selection(selection_add=[('mail','Mail')])
    pattern = fields.Char(string="Pattern",help="pattern for example customer reference in a supplier invoice, eg PO\d{5}")
    model_defaults = fields.Text()
    model_id = fields.Many2one(comodel_name="ir.model")

    @api.one
    def run(self):
        super(edi_route, self).run()
        _logger.info('run [%s:%s]' % (self.name,self.route_type))
        envelops = []
        if self.route_type == 'mail':
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
