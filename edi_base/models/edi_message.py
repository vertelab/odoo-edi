# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EdiMessage(models.Model):
    _name = 'edi.message'
    _description = 'Edi Message'

    name = fields.Char(string="Name")
    message_format_id = fields.Many2one("edi.message.format", string="Message Format", ondelete="cascade")
    payload = fields.Binary(string="Payload")
    payload_filename = fields.Char(string="Payload filename")
    consignor = fields.Many2one("res.partner", string="Consignor")
    consignee = fields.Many2one("res.partner", string="Consignee")
    sender = fields.Many2one("res.partner", string="Sender")
    receiver = fields.Many2one("res.partner", string="Receiver")
    envelope_id = fields.Many2one("edi.envelope", string="Envelope")
    res_id = fields.Integer(string='Record ID',
                            help="Database ID of record to open in form view, when ``view_mode`` is set to 'form' only")
    res_model = fields.Char(string='Destination Model',
                            help="Model name of the object to open in the view window")
    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    @api.depends('res_id', 'res_model')
    def _compute_rec_reference(self):
        for rec in self:
            if rec.res_id and rec.res_model:
                rec.reference = f"{rec.res_model},{rec.res_id}"
            else:
                rec.reference = False

    reference = fields.Reference(string='Reference', selection='_selection_target_model', compute=_compute_rec_reference)

    def pack(self):
        pass

    def unpack(self):
        pass

    
