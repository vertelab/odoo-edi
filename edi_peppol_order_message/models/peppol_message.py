#-*- coding: utf-8 -*-

#sale.order <m2o--o2m> order.message

from odoo import api, fields, models, tools,_
import logging
import base64
from io import BytesIO
from odoo.exceptions import UserError
import datetime

import xmltodict

_logger = logging.getLogger(__name__)

class PeppolMessage(models.Model):
    _name = 'peppol.message'
    _inherit = ['mail.thread']
    _description = "Peppol Message"

    name = fields.Char(string="Message Name")
    message_id = fields.Char(string="ID")
    message_type = fields.Char(string="Message Type")
    message_other_party = fields.Many2one(comodel_name='res.partner', string="Other Party")
    message_reference = fields.Reference(selection=[('sale.order', 'Sale'), 
                                                    ('purchase.order', "Purchase")], string="Message Reference")
    document = fields.Binary(string="Document")
    document_name = fields.Char(string="Document Filename", default="test.xml")
    exchange_type = fields.Selection([('outgoing', 'Outgoing'), ('incoming', 'Incoming')], string="Exchange Type")
            
    def load_buyer_customer_party(self, data_dict, vals):
        # Checks if the order contains the BuyerCustomerParty information, else raise an error
        try:
            buyer_party = self.env['res.partner'].search([('company_registry', '=', data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text'])])

            for partner in buyer_party:
                if partner.type == "contact":
                    if data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:Contact']:
                        if partner.name == data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:Contact']['cbc:Name']:
                            vals['partner_id'] = partner.id
                            break
        except Exception as e:
            raise UserError(_(f'The BuyerCustomerParty segement of the XML is incomplete, and missing crucial information about the order, specifically : {e}'))

    def load_seller_supplier_party(self, data_dict, vals):
        seller_supplier_party_id = data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text']

        seller_company = self.env['res.company'].search([('company_registry', '=', f'{seller_supplier_party_id}')])

        if seller_company:
            vals['company_id'] = seller_company.id
            _logger.info(f'{seller_company.name}')
        else:
            raise UserError(_(f"Can't find the Seller of this peppol message with the id, to this Odoo instance : {seller_supplier_party_id}"))

    def load_issue_date(self, data_dict, vals):
        # Checks if the order contains the IssueDate, if it does it will add it to the vals dictionary, and if not it will raise an error
        try:
            vals['date_order'] =  data_dict['Order']['cbc:IssueDate']
        except Exception as e:
            raise UserError(_('The order message is missing issue date'))

    def load_validity_date(self, data_dict, vals):
        # Checks if there is a validity end date, add it, otherwise don't
        try:
            vals['validity_date'] = data_dict['Order']['cac:ValidityPeriod']['cbc:EndDate']
        except Exception as e:
            vals['validity_date'] = False
            # TODO: Maybe raise an error that there is missing validity date

    def load_order_currency(self, data_dict, vals):
        # Find the currency of the peppol message and match it to the currency that the Odoo instance have
        try:
            peppol_currency = data_dict['Order']['cbc:DocumentCurrencyCode']['#text']

            pricelist = self.env['product.pricelist'].search(['&', ('currency_id', '=', peppol_currency), ('company_id', '=', self.env.company.id)])
            
            if pricelist:
                _logger.info(pricelist)
                vals['pricelist_id'] = pricelist.id
            else:
                _logger.info(f"No pricelist found for currency {peppol_currency} and company {self.env.company.id}")

        except Exception as e:
            raise UserError(_('The order message is missing currency information, error : {e}'))
            
    def load_delivery_location(self, data_dict, vals):
        try:
            buyer_party = self.env['res.partner'].search([('company_registry', '=', data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text'])])

            #FIXME: Doesn't fix the issue if the contact to the delivery is missing, than perhaps just add the delivery location, and not the contact, or raise error that there is missing information

            if len(buyer_party) > 0:
                vals['partner_shipping_id'] = buyer_party[0].id
            elif len(buyer_party) == 1:
                vals['partner_shipping_id'] = buyer_party.id
            else:
                raise UserError(_('The order message is we are missing this contact in this peppol order, in our database'))
        except Exception as e:
            raise UserError(_('The order message is missing the delivery location, error : {e}'))

    def load_invoice_address(self, data_dict, vals):
        try:
            # Invoice Address
            
            buyer_party = self.env['res.partner'].search(['&', ('company_registry', '=', data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text']), ('complete_name', '=', data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:RegistrationName'])])

            #FIXME: Doesn't fix the issue if the contact to the delivery is missing, than perhaps just add the delivery location, and not the contact, or raise error that there is missing information

            vals['partner_invoice_id'] = buyer_party[0].id

            # for partner in buyer_party:
            #     if partner.type == "company":
            #         if data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']:
            #             if partner.name == data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:RegistrationName']:
            #                 vals['partner_invoice_id'] = partner.id
            #                 break
        except Exception as e:
            raise UserError(_('Issue getting the invoice address, error : {e}'))
            pass

    def load_order_lines(self, data_dict, vals):
        # TODO: Take the right tax for the order line
        try:
            order_lines = []
            if len(data_dict['Order']['cac:OrderLine']) > 1:
                for line_item in data_dict['Order']['cac:OrderLine']:

                    _logger.info(line_item)

                    # FIXME : Make a check that there isn't multiple article numbers in the list of products.
                    # if len(self.env['product.product'].search([('default_code', '=', line_item['cac:LineItem']['cac:Item']['cac:SellersItemIdentification']['cbc:ID'])])) > 1:
                    #     # TODO: Raise an error, because this odoo instance have two with the same seller identification number
                    #     pass

                    product_id = self.env['product.product'].search([('default_code', '=', line_item['cac:LineItem']['cac:Item']['cac:SellersItemIdentification']['cbc:ID'])]).id

                    order_lines.append( (0, 0, {'product_id' : product_id, 'product_uom_qty': line_item['cac:LineItem']['cbc:Quantity']['#text']}) )

                if len(order_lines) > 0:
                    vals['order_line'] = order_lines
                else:
                    raise UserError(_(f"Trouble reading order lines from the order message, error : OrderLine count : {len(order_lines)}, maybe there is missing data in the xml or there isn't products in our system with the order messages article numbers "))
            elif len(data_dict['Order']['cac:OrderLine']) == 1:
                line_item = data_dict['Order']['cac:OrderLine']

                # if len(self.env['product.product'].search([('default_code', '=', line_item['cac:LineItem']['cac:Item']['cac:SellersItemIdentification']['cbc:ID'])])) > 1:
                #         # TODO: Raise an error, because this odoo instance have two with the same seller identification number
                #         pass

                product_id = self.env['product.product'].search([('default_code', '=', line_item['cac:LineItem']['cac:Item']['cac:SellersItemIdentification']['cbc:ID'])]).id

                order_lines.append( (0, 0, {'product_id' : product_id, 'product_uom_qty': line_item['cac:LineItem']['cbc:Quantity']['#text']}) )

                if len(order_lines) > 0:
                    vals['order_line'] = order_lines
                else:
                    raise UserError(_(f"Trouble reading order lines from the order message, error : OrderLine count : {len(order_lines)}, maybe there is missing data in the xml or there isn't products in our system with the order messages article numbers "))

            else:
                pass
        except Exception as e:
            raise UserError(_(f"Error: {e}"))   #TODO: Maybe add a better description to the error message

    def load_delivery_commitment(self, data_dict, vals):
        
        try:
            vals['commitment_date'] = data_dict['Order']['cac:Delivery']['cac:RequestedDeliveryPeriod']['cbc:StartDate']
        except:
            pass

    def unpack(self, peppol_file, peppol_file_name, record):
        xml_data = base64.b64decode(peppol_file)
        xml_file = BytesIO(xml_data)
        xml_content = xml_file.read().decode('utf-8')

        data_dict = xmltodict.parse(xml_content)
        
        # Required Data:
        # - Order Type
        # - Issue date
        # - Currency
        # - Company ID - Seller, us
        # - Company ID - Buyer, them
        # - Delivery Information : Location
        # - Atleast one OrderLine
        vals = {}

        # Checks if the type of the message is an Order, if not raise an error, since we don't have support yet to read other message types too.
        if list(data_dict)[0] != 'Order':
            #TODO: Raise an error in the future
            return

        # Checks if order is related to your company, if it is then do stuff with it, otherwise call an error, because you have someone else order message
        try:
            if self.env.company.company_registry != data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text']:
                # FIXME: In the future, dont stop the process and instead flag it, maybe dont contain the xml, can contain secret orders
                raise UserError(_("This is order message isn't for us, it's for someone else company"))
                return
        except:
            raise UserError(_("This is order message is missing crucial information, and can't be read, specifically SellerSupplierParty"))
            return

        self.load_buyer_customer_party(data_dict, vals)
        self.load_seller_supplier_party(data_dict, vals)
        self.load_issue_date(data_dict, vals)
        self.load_validity_date(data_dict, vals)
        self.load_order_currency(data_dict, vals)
        self.load_delivery_location(data_dict, vals)
        self.load_invoice_address(data_dict, vals)
        self.load_delivery_commitment(data_dict, vals)
        self.load_order_lines(data_dict, vals)

        sale_id = self.env['sale.order'].create(vals)

        message_id = data_dict['Order']['cbc:ID']
        message_type = list(data_dict)[0]
        buyer_name = data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:RegistrationName']

        record.write({  'name': f"{message_id} - {message_type} - {buyer_name}", 
                        'message_id':message_id, 
                        'message_type':message_type, 
                        'message_other_party': vals['partner_id'], 
                        'document': peppol_file,
                        'document_name' : peppol_file_name,
                        'message_reference': f"sale.order,{sale_id.id}",
                        'exchange_type': "incoming"}
                        )
        return

    def set_general_information(self, data_dict, purchase_order):
        data_dict['Order']['cbc:ID'] = purchase_order.name
        data_dict['Order']['cbc:IssueDate'] = datetime.datetime.now().strftime("%Y-%m-%d")
        data_dict['Order']['cbc:IssueTime'] = datetime.datetime.now().strftime("%H:%M:%S")
        data_dict['Order']['cac:ValidityPeriod']['cbc:EndDate'] = purchase_order.date_order.strftime("%Y-%m-%d")
        data_dict['Order']['cbc:DocumentCurrencyCode']['#text'] = purchase_order.currency_id.name

    def set_buyer_information(self, data_dict, purchase_order):
        buyer_tax_id = ''   # TODO : Add support for adding tax info to the document 

        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cbc:EndpointID']['@schemeID'] = purchase_order.company_id.peppol_eas
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cbc:EndpointID']['#text'] = purchase_order.company_id.peppol_endpoint

        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['@schemeID'] = purchase_order.company_id.peppol_eas
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text'] = purchase_order.company_id.peppol_endpoint

        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyName']['cbc:Name'] = purchase_order.company_id.name

        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:RegistrationName'] = purchase_order.company_id.name
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:CompanyID']['@schemeID'] = purchase_order.company_id.peppol_eas
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:CompanyID']['#text'] = purchase_order.company_id.peppol_endpoint

        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cac:RegistrationAddress']['cbc:StreetName'] = purchase_order.company_id.street
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cac:RegistrationAddress']['cbc:CityName'] = purchase_order.company_id.city
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cac:RegistrationAddress']['cbc:PostalZone'] = purchase_order.company_id.zip
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cac:RegistrationAddress']['cbc:CountrySubentity'] = purchase_order.company_id.state_id.name
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cac:RegistrationAddress']['cac:Country']['cbc:IdentificationCode']['#text'] = purchase_order.company_id.country_code

        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:Contact']['cbc:Name'] = purchase_order.user_id.partner_id.name
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:Contact']['cbc:Telephone'] = purchase_order.user_id.partner_id.phone
        data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:Contact']['cbc:ElectronicMail'] = purchase_order.user_id.partner_id.email

    def set_seller_information(self, data_dict, purchase_order):
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cbc:EndpointID']['@schemeID'] = purchase_order.partner_id.peppol_eas
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cbc:EndpointID']['#text'] = purchase_order.partner_id.peppol_endpoint

        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['@schemeID'] = purchase_order.partner_id.peppol_eas
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PartyIdentification']['cbc:ID']['#text'] = purchase_order.partner_id.peppol_endpoint

        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PostalAddress']['cbc:StreetName'] = purchase_order.partner_id.street
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PostalAddress']['cbc:CityName'] = purchase_order.partner_id.city
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PostalAddress']['cbc:PostalZone'] = purchase_order.partner_id.zip
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PostalAddress']['cbc:CountrySubentity'] = purchase_order.partner_id.state_id.name
        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PostalAddress']['cac:Country']['cbc:IdentificationCode']['#text'] = purchase_order.partner_id.country_code

        data_dict['Order']['cac:SellerSupplierParty']['cac:Party']['cac:PartyLegalEntity']['cbc:RegistrationName'] = purchase_order.partner_id.name

    def set_delivery_information(self, data_dict, purchase_order):
        # TODO : Retrieve the delivery location from a seperate field somewhere, but for now im taking the delivery location from just the Buyer

        data_dict['Order']['cac:Delivery']['cac:RequestedDeliveryPeriod']['cbc:StartDate'] = purchase_order.date_planned.strftime("%Y-%m-%d")
        data_dict['Order']['cac:Delivery']['cac:RequestedDeliveryPeriod']['cbc:EndDate'] = purchase_order.date_planned.strftime("%Y-%m-%d")

        # if purchase_order.dest_address_id != False and purchase_order.dest_address_id != "":
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:StreetName'] = purchase_order.dest_address_id.street
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:CityName'] = purchase_order.dest_address_id.city
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:PostalZone'] = purchase_order.dest_address_id.zip
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:CountrySubentity'] = purchase_order.dest_address_id.state_id.name
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cac:Country']['cbc:IdentificationCode'] = purchase_order.dest_address_id.country_code

        #     data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:Contact']['cbc:Name'] = purchase_order.dest_address_id.name
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:Contact']['cbc:Telephone'] = purchase_order.dest_address_id.phone
        #     data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:Contact']['cbc:ElectronicMail'] = purchase_order.dest_address_id.email
        #     return

        data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:StreetName'] = purchase_order.company_id.partner_id.street
        data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:CityName'] = purchase_order.company_id.partner_id.city
        data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:PostalZone'] = purchase_order.company_id.partner_id.zip
        data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cbc:CountrySubentity'] = purchase_order.company_id.partner_id.state_id.name
        data_dict['Order']['cac:Delivery']['cac:DeliveryLocation']['cac:Address']['cac:Country']['cbc:IdentificationCode'] = purchase_order.company_id.partner_id.country_code
        
        data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:PartyName']['cbc:Name'] = purchase_order.company_id.partner_id.name

        data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:Contact']['cbc:Name'] = purchase_order.company_id.partner_id.name
        data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:Contact']['cbc:Telephone'] = purchase_order.company_id.partner_id.phone
        data_dict['Order']['cac:Delivery']['cac:DeliveryParty']['cac:Contact']['cbc:ElectronicMail'] = purchase_order.company_id.partner_id.email

    def set_order_lines_information(self, data_dict, purchase_order):
        line_list = []
        index = 1
        data_dict['Order'].update({ 'cac:OrderLine': [] })

        if len(purchase_order.order_line) > 0:
            for line in purchase_order.order_line:
                data_dict['Order']['cac:OrderLine'].append({'cac:LineItem': { 'cbc:ID': f'{index}' } })

                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem'].update({ 'cbc:Quantity': {'@unitCode' : 'NAR', '@unitCodeListID':'UNECERec20', '#text': str(line.product_qty)} })
                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem'].update({'cbc:LineExtensionAmount' : {'@currencyID': data_dict['Order']['cbc:DocumentCurrencyCode']['#text'], '#text': str(line.price_total)}})
                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem'].update({ 'cac:Price': { 'cbc:PriceAmount': {'@currencyID': data_dict['Order']['cbc:DocumentCurrencyCode']['#text'], '#text': str(line.price_unit)}}})
                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem'].update({ 'cac:Item': {}})

                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem']['cac:Item'].update({'cbc:Description': line.product_id.description if line.product_id.description != False or line.product_id.description == "" else line.product_id.name})
                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem']['cac:Item'].update({'cbc:Name': line.product_id.name})
                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem']['cac:Item'].update({'cac:SellersItemIdentification': {'cbc:ID' : line.product_id.default_code }})

                tax_scheme_id = 'S' # TODO: Add an field in account.tax with all the different codes in UNCL5305 table

                tax_scheme_id = str(line.taxes_id.classified_tax_category).upper()

                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem']['cac:Item'].update({'cac:ClassifiedTaxCategory': {'cbc:ID' : {'@schemeID': 'UNCL5305', '#text': tax_scheme_id} }})
                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem']['cac:Item']['cac:ClassifiedTaxCategory'].update({'cbc:Percent': str(line.taxes_id.amount)})

                data_dict['Order']['cac:OrderLine'][index-1]['cac:LineItem']['cac:Item']['cac:ClassifiedTaxCategory'].update({'cac:TaxScheme': { 'cbc:ID': 'VAT'}})

                index = index + 1
        else:
            raise UserError(_("This purchase order doesn't have any items that are being purchased"))

    def set_tax_total_information(self, data_dict, purchase_order):
        data_dict['Order']['cac:TaxTotal']['cbc:TaxAmount']['@currencyID'] = data_dict['Order']['cbc:DocumentCurrencyCode']['#text']
        data_dict['Order']['cac:TaxTotal']['cbc:TaxAmount']['#text'] = str(purchase_order.amount_tax)

    def set_anticipated_monetary_total(self, data_dict, purchase_order):
        data_dict['Order']['cac:AnticipatedMonetaryTotal']['cbc:LineExtensionAmount']['@currencyID'] = data_dict['Order']['cbc:DocumentCurrencyCode']['#text']
        data_dict['Order']['cac:AnticipatedMonetaryTotal']['cbc:LineExtensionAmount']['#text'] = str(purchase_order.amount_untaxed)

        data_dict['Order']['cac:AnticipatedMonetaryTotal']['cbc:PayableAmount']['@currencyID'] = data_dict['Order']['cbc:DocumentCurrencyCode']['#text']
        data_dict['Order']['cac:AnticipatedMonetaryTotal']['cbc:PayableAmount']['#text'] = str(purchase_order.amount_total)

    def pack(self, purchase_order):

        xml_template = tools.misc.file_path("edi_peppol_order_message/static/src/xml/peppol_order_template.xml")

        if purchase_order == False:
            return

        with open(xml_template, 'r') as file:
            xml_content = file.read()

            data_dict = xmltodict.parse(xml_content)

            # Check what this order status is, is it a purchase order, map it and save it as a xml, if not just call an error that this is not a purchase order yet
            if purchase_order.state != "cancel":

                self.set_general_information(data_dict, purchase_order)
                self.set_buyer_information(data_dict, purchase_order)
                self.set_seller_information(data_dict, purchase_order)
                self.set_delivery_information(data_dict, purchase_order)
                self.set_order_lines_information(data_dict, purchase_order)
                self.set_tax_total_information(data_dict, purchase_order)
                self.set_anticipated_monetary_total(data_dict, purchase_order)

                xml = xmltodict.unparse(data_dict, pretty=True)

                output_xml = xml.encode('utf-8')
                output_xml_encoded = base64.b64encode(output_xml)

                message_id = data_dict['Order']['cbc:ID']
                message_type = list(data_dict)[0]
                buyer_name = data_dict['Order']['cac:BuyerCustomerParty']['cac:Party']['cac:PartyLegalEntity']['cbc:RegistrationName']

                file_name = f'peppol_order_{message_id}.xml'

                self.env['peppol.message'].create({ 'name': f"{message_id} - {message_type} - {buyer_name}", 
                                                    'message_id':message_id, 
                                                    'message_type':message_type, 
                                                    'message_other_party': purchase_order.partner_id.id, 
                                                    'document': output_xml_encoded,
                                                    'document_name': file_name,
                                                    'message_reference': f"purchase.order,{purchase_order.id}",
                                                    'exchange_type': "outgoing"}
                                                    )

                attachment = self.env['ir.attachment'].sudo().create({
                    'name': file_name,
                    'type': 'binary',
                    'datas': output_xml_encoded,
                    'mimetype': 'application/xml',
                    'res_model': 'mail.mail',
                    'res_id': False,
                })

                mail_from = purchase_order.user_id.email
                mail_to = purchase_order.partner_id.email

                mail_vals = {
                    'subject': f'Peppol Order : {message_id}',
                    'body_html': '',
                    'email_to': mail_to,
                    'auto_delete': False,
                    'email_from': mail_from,
                    'attachment_ids': [(4, attachment.id)],
                }

                mail_id = self.env['mail.mail'].sudo().create(mail_vals)
                mail_id.sudo().send()

            else:
                raise UserError(_("This order can't be handled, it's canceled"))
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        record = super(PeppolMessage, self).message_new(msg_dict, custom_values)

        peppol_message_xml_data = base64.b64encode(msg_dict['attachments'][0].content)

        self.unpack(peppol_message_xml_data, msg_dict['attachments'][0].fname, record)

        return record