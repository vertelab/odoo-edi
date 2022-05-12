#from datetime import date, datetime
#import datetime
#import os, logging, csv, inspect
#from jmespath import search
#from lxml.etree import Element, SubElement, QName, tostring
#from lxml.isoschematron import Schematron

import logging

from lxml import etree

from odoo import models, api, _, fields
from odoorpc import ODOO


_logger = logging.getLogger(__name__)

# TODO: This should be a central class, not a 'local' on.
class NSMAPS:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, None:empty}

    XNS={'cac':cac,
         'cbc':cbc}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


# This class handles spesificly the conversion of a Odoo Invoice, to a PEPPOL Invoice.
class Peppol_To_Invoice(models.Model):
    _name = "peppol.toinvoice"
    _inherit = "peppol.topeppol"
    _description = "Module for converting invoice from Odoo to PEPPOL"

    #Base function for converting a Odoo Invoice, to a PEPPOL Invoice.
    def create_invoice(self):
        currency = self.currency_id.name
        invoice = etree.Element("Invoice", nsmap=NSMAPS.NSMAP)

        self.convert_field(invoice, 'Invoice', 'CustomizationID',
                           text='urn:cen.eu:en16931:2017#compliant#' +
                                'urn:fdc:peppol.eu:2017:poacc:billing:3.0')
        # TODO: the ProfileID should not be static?
        self.convert_field(invoice, 'Invoice', 'ProfileID',
                           text='urn:fdc:peppol.eu:2017:poacc:billing:04:1.0')
        self.convert_field(invoice, 'Invoice', 'ID',
                           text=self.name)
        self.convert_field(invoice, 'Invoice', 'IssueDate',
                           text=self.invoice_date)
        self.convert_field(invoice, 'Invoice', 'DueDate',
                           text=self.invoice_date_due)
        # TODO: InvoiceTypeCode should maybe not be static?
        self.convert_field(invoice, 'Invoice',
                           'InvoiceTypeCode', text='380')
        #Not handled: Note: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-Note/
        #Not handled: TaxPointDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-TaxPointDate/
        self.convert_field(invoice, 'Invoice', 'DocumentCurrencyCode',
                           text=self.currency_id.name)
        #Not handled: TaxCurrencyCode: Does this exist? Maybe in the account.move.line? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-TaxCurrencyCode/
        #Not handled: AccountingCost: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-AccountingCost/
        #TODO: BuyersReferance should not be static!
        self.convert_field(invoice, 'Invoice', 'BuyerReference',
                           text='abs1234')

        #Invoice Period Instructions
        #Not handled: InvoicePeriod/StartDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoicePeriod/cbc-StartDate/
        #Not handled: InvoicePeriod/EndDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoicePeriod/cbc-EndDate/
        #Not handled: InvoicePeriod/DescriptionCode: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoicePeriod/cbc-DescriptionCode/

        #Order Reference Instructions
        #This is wrong and does not work. purchase_id refers to autocomplete and not a previous order. self.convert_field(invoice, 'Invoice/cac:OrderReference', 'ID', datamodule='account.move.purchase_id,purchase.order.name') 
        #Not handled: OrderReference/SalesOrderID: maybe something to do with account.move.purchase_id,purchase.order.order_line? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-OrderReference/cbc-SalesOrderID/

        #BillingRefernce
        #Not handled: BillingReference/InvoiceDocumentReference/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-BillingReference/cac-InvoiceDocumentReference/cbc-ID/
        #Not handled: BillingReference/InvoiceDocumentReference/IssueDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-BillingReference/cac-InvoiceDocumentReference/cbc-IssueDate/

        #None of the below are handled
            #DespatchDocumentReference
            #ReceiptDocumentReference
            #OriginatorDocumentReference
            #ContractDocumentReference
            #AdditionalDocumentReference
            #ProjectReference
        #None of the above are handled

        #Accounting Supplier Party Instructions
        self.convert_party(invoice,
                           'Invoice/cac:AccountingSupplierParty',
                           self.company_id)

        #Accounting Customer Party Instructions
        self.convert_party(invoice,
                           'Invoice/cac:AccountingCustomerParty',
                           self.partner_id)

        #PayeeParty, is this even possible in Odoo?

        #TaxRepresentativeParty, is this even possible in Odoo?

        #Delivery Instructions
        #Not Handled: Delivery/ActualDeliveryDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-Delivery/cbc-ActualDeliveryDate/
        #Not Handled: Delivery/DeliveryLocation/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-Delivery/cac-DeliveryLocation/cbc-ID/
        self.convert_address(invoice,
                            'Invoice/cac:Delivery/cac:DeliveryLocation/cac:Address',
                            self.partner_shipping_id)
        #Not Handled: Delivery/DeliveryParty/PartyName/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-Delivery/cac-DeliveryParty/cac-PartyName/cbc-Name/

        #PaymentMeans, these seem important but can't find them in Odoo.

        #Payment Terms Instruction
        self.convert_field(invoice, 'Invoice/cac:PaymentTerms','Note',
                           text=self.narration)
        #AllowanceCharge, is this even possible in Odoo?

        #Tax Total Instructions
        self.convert_field(invoice, 'Invoice/cac:TaxTotal', 'TaxAmount',
                           text=self.amount_tax,
                           attri='currencyID:'+currency)

        for vat_rate in self.get_all_different_vat_rates():
            new_tax_subtotal = etree.Element(etree.QName(NSMAPS.NSMAP['cac'],
                                             'TaxSubtotal'),
                                             nsmap=NSMAPS.NSMAP)
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal', 'TaxableAmount',
                               text=self.get_taxable_amount_for_vat_rate(vat_rate[0]),
                               attri='currencyID:'+currency)
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal', 'TaxAmount',
                               text=self.get_tax_amount_for_vat_rate(vat_rate[0]),
                               attri='currencyID:'+currency)
            #TODO: The below lines should be set based on the account-move.line.tax_ids. However, in it you can only find the information one wants in the 'name', which is in swedish. Is there a solution to this?
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal/cac:TaxCategory', 'ID',
                               text=vat_rate[1])
            #TaxExemptionReasonCode
            #TaxExemptionReason
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal/cac:TaxCategory', 'Percent',
                               text=vat_rate[0])
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme',
                               'ID', text='VAT')
            invoice.xpath('/Invoice/cac:TaxTotal',
                          namespaces=NSMAPS.XNS)[0].append(new_tax_subtotal)

        #Legal Monetary Total
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'LineExtensionAmount',
                           text=str(self.get_line_extension_amount()),
                           attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'TaxExclusiveAmount',
                           text=self.amount_untaxed,
                           attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'TaxInclusiveAmount',
                           text=self.amount_total,
                           attri='currencyID:'+currency)
        #Not Handled: LegalMonetaryTotal/AllowanceTotalAmount: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-LegalMonetaryTotal/cbc-AllowanceTotalAmount/
        #Not Handled: LegalMonetaryTotal/ChargeTotalAmount: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-LegalMonetaryTotal/cbc-ChargeTotalAmount/
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'PrepaidAmount',
                           text=self.get_prepaid_amount(),
                           attri='currencyID:'+currency)
        #Not Handled: LegalMonetaryTotal/PayableRoundingAmount: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-LegalMonetaryTotal/cbc-PayableRoundingAmount/
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'PayableAmount',
                           text=self.amount_residual,
                           attri='currencyID:'+currency)

        #Invoice Line
        #TODO: Instead of using 'recordset' here, it aught to be possible to enter the path to the wanted datafield using only the datamodule and the current id from 'line'.
        n = 0
        for line in self['invoice_line_ids']:
            n += 1
            new_line = etree.Element(etree.QName(NSMAPS.NSMAP['cac'],
                                     'InvoiceLine'),
                                     nsmap=NSMAPS.NSMAP)

            # This line prevents lines that are 'notes' or 'sections' from being handled here.
            # Meaning that only 'real' lines with a 'item' on it, is handled.
            if line.display_type != False:
                continue

            self.convert_field(new_line, 'cac:InvoiceLine', 'ID',
                               text=str(n))
            #Not Handled: InvoiceLine/Note: This does not exist built into the line, but as a seperate line. https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/
            self.convert_field(new_line, 'cac:InvoiceLine', 'InvoicedQuantity',
                               text=line.quantity,
                               attri='unitCode:C62')
            self.convert_field(new_line, 'cac:InvoiceLine', 'LineExtensionAmount',
                               text=line.price_subtotal,
                               attri='currencyID:'+currency)
            #Not Handled: InvoiceLine/AccountingCost: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cbc-AccountingCost/
            #Not Handled: InvoiceLine/InvoicePeriod/StartDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-InvoicePeriod/cbc-StartDate/
            #Not Handled: InvoiceLine/InvoicePeriod/EndDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-InvoicePeriod/
            #Not Handled: InvoiceLine/OrderLineReference/LineID: Needs an Order Referance to be handled. https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-OrderLineReference/cbc-LineID/
            #Not Handled: InvoiceLine/DocumentReference: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-DocumentReference/
            #Not Handled: InvoiceLine/AllowanceCharge: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-AllowanceCharge/
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item', 'Description',
                               text=line.name)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item', 'Name',
                               text=line.product_id.name)
            #Not Handled: InvoiceLine/Item/BuyersItemIdentification/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-Item/cac-BuyersItemIdentification/cbc-ID/
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:SellersItemIdentification',
                               'ID',
                               text=line.product_id.default_code)
            #Not Handled: InvoiceLine/Item/StandardItemIdentification/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-Item/cac-StandardItemIdentification/cbc-ID/
            #Not Handled: InvoiceLine/Item/OriginCountry/IdentificationCode: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-Item/cac-OriginCountry/cbc-IdentificationCode/
            #Not Handled: InvoiceLine/Item/CommodityClassification/ItemClassificationCode: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-Item/cac-CommodityClassification/cbc-ItemClassificationCode/
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory',
                               'ID',
                               text=self.translate_tax_category_to_peppol(line.tax_ids.name))
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory',
                               'Percent',
                               text=line.tax_ids.amount)
            self.convert_field(new_line,
                               'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory/cac:TaxScheme',
                               'ID',
                               text='VAT')
            #Not Handled: InvoiceLine/Item/AdditionalItemProperty: Do these exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-Item/cac-AdditionalItemProperty/
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Price', 'PriceAmount',
                               text=(line.price_subtotal / line.quantity),
                               attri='currencyID:'+currency)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Price', 'BaseQuantity',
                               text='1',
                               attri='unitCode:C62')
            #Not Handled: InvoiceLine/Price/AllowanceCharge: Do these exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-Price/cac-AllowanceCharge/

            invoice.append(new_line)

    #Cleanup
        if self.remove_empty_elements(invoice) is None:
            return None

        return invoice

    # Helper Functions that are used only by the Odoo Invoice, to PEPPOL Invoice conversions.
    def get_line_extension_amount(self):
        amount = 0
        for line in self['invoice_line_ids']:
            amount += line.price_subtotal
        return amount

    def get_prepaid_amount(self):
        prepaid_amount = (self.amount_total - self.amount_residual)
        if prepaid_amount == 0:
            prepaid_amount = None
        return prepaid_amount

    def get_all_different_vat_rates(self):
        unique_vats = set()
        for line in self['invoice_line_ids']:
            if line.display_type == False:
                unique_vats.add((line.tax_ids.amount,
                                 self.translate_tax_category_to_peppol(line.tax_ids.name)))
        return unique_vats

    def get_taxable_amount_for_vat_rate(self, vat_rate):
        taxable_amount = 0
        for line in self['invoice_line_ids']:
            if line.tax_ids.amount == vat_rate:
                taxable_amount += line.price_subtotal
        return taxable_amount

    def get_tax_amount_for_vat_rate(self, vat_rate):
        tax_amount = 0
        for line in self['invoice_line_ids']:
            if line.tax_ids.amount == vat_rate:
                tax_amount += (line.price_total - line.price_subtotal)
        return tax_amount

    def is_vat_inclusive(self, type):
        try:
            if type[-1] == 'i' and len(type) > 1:
                return True
        except:
            pass
        return False