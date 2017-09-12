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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

import base64
import re

import logging
_logger = logging.getLogger(__name__)

class edi_envelope(models.Model):
    _inherit = 'edi.envelope'

    mail_id = fields.Many2one(comodel_name="mail.message")
    route_type = fields.Selection(selection_add=[('mail','Mail')])
    record = fields.Reference(selection=[('account.invoice', 'Invoice'),])
    
    def _check_mail_attachments(self):
        image = None
        for attachment in self.mail_id.attachment_ids:
            if attachment.mimetype == 'application/pdf':
                if not attachment.image:
                    attachment.pdf2image(800,1200)
                image = attachment.image
            elif attachment.mimetype in ['image/jpeg','image/png','image/gif'] and image == None:
                image = attachment.datas
        self.image = image
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

    @api.one
    def split(self):
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
            #~ else:
                #~ r = eval(self.route_id.model_defaults)
                #~ if self.mail_id.author_id and self.mail_id.author_id.parent_id and self.mail_id.author_id.parent_id.is_company:
                    #~ r['partner_id'] = self.mail_id.author_id.parent_id.id
                #~ if self.ref:
                    #~ r['origin'] = self.ref
                #~ r.update(self.env['account.invoice'].onchange_partner_id('in_invoice',r['partner_id'])['value'])
                #~ #raise Warning(self.env['account.invoice'].onchange_partner_id('in_invoice',self.sender.id))
                #~ record = self.env[self.route_id.model_id.model].create(r)
                #~ id = self.env['mail.message'].create({
                        #~ 'body': _("New %s \n" % ("<a href='%s'>%s</a>" % ('',self.ref))),
                        #~ 'subject': "New record",
                        #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                        #~ 'res_id': self.id,
                        #~ 'model': self._name,
                        #~ 'type': 'notification',})
                #~ id = self.env['mail.message'].create({
                        #~ 'body': _("New %s \n" % ("<a href='%s'>%s</a>" % ('',self.ref))),

                        #~ 'subject': "New record",
                        #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                        #~ 'res_id': record.id,
                        #~ 'model': record._name,
                        #~ 'type': 'notification',})
            #~ id = self.env['mail.message'].create({
                        #~ 'body': _("Mailet %s" % (self.mail_id.read())),
                        #~ 'subject': "Mailet",
                        #~ 'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                        #~ 'res_id': self.id,
                        #~ 'model': self._name,
                        #~ 'type': 'notification',})
            #~ _logger.warn('Subject %s ref %s' % (self.mail_id.subject,self.ref))  
            #~ raise Warning([a for a in self.mail_id.attachment_ids]) 
            #~ for attachment in self.mail_id.attachment_ids:
                #~ attachment.res_model = record._name
                #~ attachment.res_id = record.id
        else:
            super(edi_envelope,self).split()


class edi_envelope_invoice(models.TransientModel):

    _name ='edi.envelope.invoice'
    _description = 'Select invoice'

    invoice_ids = fields.Many2many(comodel_name="account.invoice")
    invoice_id = fields.Many2one(comodel_name="account.invoice")
    
    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, [context['active_id']], ['date_start', 'date_end', 'credit_note'])[0]
        from_date =  run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)
        credit_note = run_data.get('credit_note', False)
        if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),
                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
            }
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}



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

    @api.one
    def run(self):
        super(edi_route, self).run()
        _logger.info('run [%s:%s]' % (self.name,self.route_type))
        envelops = []
        if self.route_type == 'mail':
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: