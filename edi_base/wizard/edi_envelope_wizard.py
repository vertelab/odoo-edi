from odoo import models, fields, api
import base64

class FileUploadEnvelopeWizard(models.TransientModel):
    _name = 'file.upload.envelope.wizard'
    _description = 'Upload a edi envelope File Wizard'

    file_data = fields.Binary(string='Upload File', required=True)
    file_name = fields.Char(string='File Name')

    def unpack(self):
        envelope = self.env['edi.envelope'].create({'name':self.file_name,'payload':self.file_data})
        envelope.unfold()
        return {'type': 'ir.actions.act_window_close'}
