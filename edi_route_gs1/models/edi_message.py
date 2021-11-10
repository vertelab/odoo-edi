# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
import base64
from datetime import datetime

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _inherit = "edi.message"

    def _pack(self):
        super(EdiMessage, self)._pack()
        if self.edi_type.id == self.env.ref('edi_route_gs1.edi_message_type_gs1').id:
            if self.model_record._name != 'stock.picking':
                raise ValueError(
                    "GS1: Attached record is not a stock.pack! {model}".format(model=self.model_record._name),
                    self.model_record._name)
            picking = self.model_record
            msg = self.UNH('GS1')
            msg += self.BGM(doc_code=351,
                            doc_no=picking.name)  # Possibly should use GDTI, Global Document Type Identifier
            # Document date
            msg += self.DTM(137)
            # Despatch DT
            msg += self.DTM(11, picking.min_date)
            # Estimated Delivery DT
            msg += self.DTM(17, picking.date_done)
            # Order reference
            if picking.sale_id:
                msg += self.RFF(picking.sale_id.client_order_ref or picking.sale_id.name, qualifier='ON')
            msg += self.NAD_SU()
            # Godsavsändare
            # Not allowed by Coop.
            # ~ if po:
            # ~ self.forwarder_id = po.partner_id
            # ~ msg += self.NAD_SH()
            # Ship from location. Used when buyer picks up the goods.
            # Not implemented
            # msg += self._NAD('SF', shipping_partner)

            # Buyer identification
            msg += self.NAD_BY(picking.sale_id.partner_id)
            # Consignee identification. Used if recipient is other than buyer.
            # msg += self.NAD_CN()
            # Delivery place. Used if delivered to other place than recipient adress.
            # Mandatory according to Coop
            msg += self._NAD('DP', picking.sale_id.partner_id)
            # Mode of transport
            # Not implemented.
            # msg += self.TDT()
            # ~ 10   Sjötransport
            # ~ Koden ska användas så fort transportfordonet gör någon del av resan till sjöss.
            # ~ 20   Tågtransport
            # ~ 30   Vägtransport
            # ~ 40   Flygtransport
            # ~ 50   Postfrakt
            # ~ Koden finns med av praktiska skäl, trots att postfrakt inte är ett egentligt transportsätt. I många fall vet exportören eller importören inte med vilket transportsätt gods som fraktats per post har korsat gränsen.
            # ~ 60   Mer än ett transportsätt
            # ~ Koden används när godset fraktas med minst två olika transportsätt på basis av ett transportkontrakt.
            # ~ 70   Transport via fasta anläggningar
            # ~ Koden används för transport via t.ex. pipeline eller elledningar.
            # ~ 100  Transport via bud (EAN-kod)
            # ~ Koden används när en budtjänst har anlitats för att hämta och leverera en försändelse
            level = 0
            qty_total = 0
            moves = picking.move_lines

            packages = self.env['stock.quant.package'].browse()
            for operation in picking.pack_operation_ids:
                packages |= operation.result_package_id

            for package in packages:
                level += 1
                msg += self.CPS(level)
                # Only supports pallets for now
                msg += self.PAC()
                # Use SSCC from lot/serial number
                if package.sscc:
                    msg += self.PCI()
                    msg += self.GIN(package.sscc)
                for quant in package.quant_ids:
                    msg += self.LIN(quant)
                    msg += self.PIA(quant.product_id, 'SA')
                    # Batch number
                    if quant.lot_id and quant.lot_id.name:
                        msg += self.PIA(quant.lot_id.name, 'NB')
                    msg += self.QTY(quant)
                    qty_total += quant.qty
                    # Use by date
                    if quant.lot_id and quant.lot_id.life_date:
                        msg += self.DTM(361, quant.lot_id.life_date)
                    # Order reference with line nr
                    order_line = None
                    for line in picking.sale_id.order_line:
                        if line.product_id == quant.product_id:
                            order_line = line
                            break
                    if order_line:
                        # Order Reference
                        msg += self.RFF(picking.sale_id.client_order_ref or picking.sale_id.name, 'ON',
                                        order_line.sequence)
                        # Quantity Difference from ORDRSP
                        move = self._edi_get_move_for_product(quant.product_id, picking)
                        diff = move.product_uom_qty - order_line.product_uom_qty
                        if diff != 0:
                            msg += self.QVR(diff, move.qty_difference_reason or 'AV')
                        moves -= move
                # Undelivered Products are registered in last pallet.
                if level == len(packages):
                    order_line = None
                    for move in moves:
                        for line in picking.sale_id.order_line:
                            if line.product_id == move.product_id:
                                order_line = line
                                break
                        diff = move.product_uom_qty - order_line.product_uom_qty
                        if diff != 0:
                            msg += self.LIN(move)
                            msg += self.PIA(move.product_id, 'SA')
                            msg += self.QTY(move)
                            msg += self.RFF(picking.sale_id.client_order_ref or picking.sale_id.name, 'ON',
                                            order_line.sequence)
                            msg += self.QVR(diff, move.qty_difference_reason or 'AV')
            msg += self.CNT(1, qty_total)
            msg += self.CNT(2, self._lin_count)
            msg += self.UNT()
            self.body = base64.b64encode(self._gs1_encode_msg(msg))

    def _unpack(self):
        return super(EdiMessage, self)._unpack()
