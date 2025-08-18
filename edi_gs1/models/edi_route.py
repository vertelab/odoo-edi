from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class EdiRoute(models.Model):
    _inherit = 'edi.route'

    def _process_edi_route(self, rec):
        # for line in self.route_line_ids.filtered(lambda x: x.res_model == rec._name):
        try:
            message = self.env['edi.message'].pack(rec=rec)
            if message:
                _logger.info(f"✓ Packed {rec._name} {rec.id} into message {message.name}")
        except Exception as e:
            _logger.error(f"Failed to pack {rec._name} {rec.id}: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('EDI Packing Failed'),
                    'message': _(f'{e}'),
                    'type': 'danger',
                }
            }
        return True

    def action_pack_edi_message(self):
        """Pack records into EDI messages based on route configuration"""
        partner_ids = self.env['res.partner'].search([('route_id', '!=', False)])

        for partner in partner_ids:
            _logger.info(f"Processing EDI route for partner: {partner.name}")

            for line in partner.route_id.route_line_ids:
                # Build domain for this route line
                domain = [('partner_id', '=', partner.id), ('move_type', '=', 'in_invoice')]
                domain += eval(line.domain)

                # Find records matching the domain
                rec_ids = self.env[line.res_model].search(domain)
                _logger.info(f"Found {len(rec_ids)} records for {line.res_model}")

                # Pack each record into EDI message
                for rec in rec_ids:
                    try:
                        message = self.env['edi.message'].pack(rec=rec)
                        if message:
                            _logger.info(f"✓ Packed {rec._name} {rec.id} into message {message.name}")
                    except Exception as e:
                        _logger.error(f"Failed to pack {rec._name} {rec.id}: {str(e)}")
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('EDI Packing Failed'),
                                'message': _(f'{e}'),
                                'type': 'danger',
                            }
                        }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('EDI Packing Complete'),
                'message': _('Records have been packed into EDI messages.'),
                'type': 'success',
            }
        }


class EdiRouteLine(models.Model):
    _inherit = 'edi.route.line'

    def _get_model_selection(self):
        return [
            (model.model, model.name)
            for model in self.env['ir.model'].sudo().search([('transient', '=', False)])
        ]

    res_model = fields.Selection(selection=_get_model_selection, string="Model")


