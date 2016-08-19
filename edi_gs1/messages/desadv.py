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
import base64
from datetime import datetime
#https://www.stylusstudio.com/edifact/frames.htm

import logging
_logger = logging.getLogger(__name__)

class edi_message(models.Model):
    _inherit='edi.message'

    @api.one
    def _pack(self):
        super(edi_message, self)._pack()
        if self.edi_type.id == self.env.ref('edi_gs1.edi_message_type_desadv').id:
            if self.model_record._name != 'stock.picking':
                raise ValueError("DESADV: Attached record is not a stock.pack! {model}".format(model=self.model_record._name),self.model_record._name)
            picking = self.model_record
            #Find possible purchase and sale orders
            so = self.env['sale.order'].search([('name', '=', picking.origin)])
            po = None #Used to handle drop shipping
            if not so:
                po = self.env['purchase.order'].search([('name', '=', picking.origin)])
                if po:
                    so = self.env['sale.order'].search([('name', '=', po.origin)])
            msg = self.UNH('DESADV')
            msg += self.BGM(doc_code=351, doc_no=picking.name) #Possibly should use GDTI, Global Document Type Identifier
            #Document date
            msg += self.DTM(137)
            #Despatch DT
            msg += self.DTM(11, picking.min_date)
            #Estimated Delivery DT
            msg += self.DTM(17, picking.date_done)
            #Order reference
            if so and so.client_order_ref:
                msg += self.RFF(so.client_order_ref, qualifier='ON')
            msg += self.NAD_SU()
            #Godsavsändare
            #Not allowed by Coop.
            #~ if po:
                #~ self.forwarder_id = po.partner_id
                #~ msg += self.NAD_SH()
            #Ship from location. Used when buyer picks up the goods.
            #Not implemented
            #msg += self._NAD('SF', shipping_partner)

            #Buyer identification
            msg += self.NAD_BY()
            #Consignee identification. Used if recipient is other than buyer.
            #msg += self.NAD_CN()
            #Delivery place. Used if delivered to other place than recipient adress.
            #Mandatory according to Coop
            msg += self._NAD('DP', so.partner_id)
            #Mode of transport
            #Not implemented.
            #msg += self.TDT()
            #~ 10   Sjötransport
            #~ Koden ska användas så fort transportfordonet gör någon del av resan till sjöss.
            #~ 20   Tågtransport
            #~ 30   Vägtransport
            #~ 40   Flygtransport
            #~ 50   Postfrakt
            #~ Koden finns med av praktiska skäl, trots att postfrakt inte är ett egentligt transportsätt. I många fall vet exportören eller importören inte med vilket transportsätt gods som fraktats per post har korsat gränsen.
            #~ 60   Mer än ett transportsätt
            #~ Koden används när godset fraktas med minst två olika transportsätt på basis av ett transportkontrakt.
            #~ 70   Transport via fasta anläggningar
            #~ Koden används för transport via t.ex. pipeline eller elledningar.
            #~ 100  Transport via bud (EAN-kod)
            #~ Koden används när en budtjänst har anlitats för att hämta och leverera en försändelse
            level = 1
            qty_total = 0
            for operation in picking.pack_operation_ids:
                msg += self.CPS(level)
                level += 1
                #Only supports pallets for now
                msg += self.PAC()
                #Use SSCC from lot/serial number
                if operation.result_package_id and operation.result_package_id.sscc:
                    msg += self.PCI()
                    msg += self.GIN(operation.result_package_id.sscc)
                msg += self.LIN(operation)
                msg += self.PIA(operation.product_id, 'SA')
                #Batch number
                if operation.lot_id and operation.lot_id.name:
                    msg += self.PIA(operation.lot_id.name, 'NB')
                msg += self.QTY(operation)
                qty_total += operation.product_qty
                #Use by date
                if operation.lot_id and operation.lot_id.life_date:
                    msg += self.DTM(361, operation.lot_id.life_date)
                #Order reference with line nr
                for line in so.order_line:
                    if line.product_id == operation.product_id:
                        msg += self.RFF(so.client_order_ref, 'ON', line.sequence)
                        break
            msg += self.CNT(1, qty_total)
            msg += self.CNT(2, self._lin_count)
            msg += self.UNT()
            self.body = base64.b64encode(self._gs1_encode_msg(msg))
