from odoo import api, fields, models, tools,_
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class EdiDespatchMessage(models.Model):
    _inherit = 'edi.message'

    def _process_peppol_message(self, payload):
        if self.message_format_id.name == "urn:fdc:peppol.eu:poacc:trns:despatch_advice:3":
            return self._unpack_despatch_advice(payload)
        return super()._process_peppol_message(payload)

    def _unpack_despatch_advice(self, payload):
        # print(payload)
        order_reference = payload.get('OrderReference', {}).get('ID')
        print(order_reference)
        if purchase_order := self._get_purchase_order(order_ref=order_reference):
            picking_id = purchase_order.picking_ids.filtered(
                lambda picking: picking.state == 'assigned' and picking.picking_type_id.code == 'incoming'
            )[-1]
            print(picking_id)
            if picking_id:
                self.write({"res_model": picking_id._name, "res_id": picking_id.id})
                return picking_id.button_validate()

        # else:
        raise UserError(_("No Order found for this Order Reference"))
        # print(miracle)

    def _get_purchase_order(self, order_ref):
        return self.env['purchase.order'].search([('peppol_order_reference', '=', order_ref)], limit=1)