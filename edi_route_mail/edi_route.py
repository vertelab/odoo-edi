# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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
from odoo.exceptions import except_orm, Warning, RedirectWarning

import base64
import re

import logging
_logger = logging.getLogger(__name__)

class edi_route(models.Model):
    _inherit = 'edi.route'
    _inherits = {"mail.alias": "alias_id"}

    alias_id = fields.Many2one(comodel_name='mail.alias', string='Alias', ondelete="restrict", required=True,
                               help="Internal email associated with this route. Incoming emails are automatically synchronized")
    alias_model = fields.Char(String="Alias Model",default='edi.envelope')
    mail_debug = fields.Boolean(string="Debug",required=False)
    protocol = fields.Selection(selection_add=[('mail','Mail')])
    route_type = fields.Selection(selection_add=[('mail','Mail')])
    pattern = fields.Char(string="Pattern",help="pattern for example customer reference in a supplier invoice, eg PO\d{5}")
    model_defaults = fields.Text()
    model_id = fields.Many2one(comodel_name="ir.model")
   
    @api.multi
    def _run_in(self):
        if self.route_type == 'mail':
            return self.env['edi.envelope'].search([('state','=','progress'),('route_id','=',self.id)])
        else:
            return super(edi_route, self)._run_in()

class edi_envelope(models.Model):
    _inherit = 'edi.envelope'

    mail_id = fields.Many2one(comodel_name="mail.message")
    route_type = fields.Selection(selection_add=[('mail','Mail')])
    record = fields.Reference(selection=[])
    image = fields.Binary()
    
    def _check_mail_attachments_image(self,image=None):
        for attachment in self.mail_id.attachment_ids:
            if attachment.file_type in ['image/jpeg','image/png','image/gif'] and image == None:
                image = attachment.datas
        return image
    def _check_mail_attachments(self):
        self.image = self._check_mail_attachments_image()
    def _check_mail_pattern(self):
        txt = self.mail_id.subject + self.mail_id.body
        for attachment in self.mail_id.attachment_ids:
            txt += attachment.index_content
        m = re.search(self.route_id.pattern,txt)
        return m.group(0) if m else None


    @api.multi
    def attachment2record(self):
        for envelope in self:
            if envelope.record:
                for attachment in envelope.mail_id.attachment_ids:
                    attachment.write({'res_model': envelope.record._name,'res_id':envelope.record.id})

    def _get_record(self,record=None):
        if not record:
            return self.env[self.route_id.model_id.model].search(['|','|',('name','=',self.ref),('reference_type','=',self.ref),('origin','=',self.ref)])
        return record

    @api.one
    def _split(self):
        if self.route_id.route_type == 'mail':
            self.mail_id = self.env['mail.message'].search([('model','=','edi.envelope'),('res_id','=',self.id),('type','=','email')])
            self.sender = self.mail_id.author_id.id if self.mail_id.author_id else None
            self.route_type = self.route_id.route_type
            self._check_mail_attachments()
            if not self.ref:
                self.ref = self._check_mail_pattern()

            record = self.env[self.route_id.model_id.model].search(['|','|',('name','=',self.ref),('reference_type','=',self.ref),('origin','=',self.ref)])
            if record and len(record) == 1:
                #~ raise Warning(record,record.name,record._name)
                _logger.warn('%s %s %s' % (record,record.name,record._name))
                self.record = record
                id = self.env['mail.message'].create({
                        'body': _("Found %s by %s\n" % ("<a href='%s'>%s</a>" % ('',self.ref),self.ref)),
                        'subject': "Found record",
                        'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                        'res_id': self.id,
                        'model': self._name,
                        'type': 'notification',})
                id = self.env['mail.message'].create({
                        'body': _("Found %s by %s\n" % ("<a href='%s'>%s</a>" % ('',self.ref),self.ref)),
                        'subject': "Found record",
                        'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                        'res_id': record.id,
                        'model': record._name,
                        'type': 'notification',})
                self.attachment2record()
            self.envelope_opened()
        else:
            super(edi_envelope,self)._split()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: