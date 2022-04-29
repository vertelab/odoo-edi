#from datetime import date, datetime
import datetime
import os, logging, csv, inspect
from jmespath import search

from lxml import etree, html
from lxml.etree import Element, SubElement, QName, tostring
from lxml.isoschematron import Schematron
from odoo import models, api, _, fields
from odoorpc import ODOO

#from peppol_invoice_from_odoo import create_invoice
#from edi_peppol_validate import validate_peppol

#from lxml import etree, html

_logger = logging.getLogger(__name__)

class XMLNamespaces:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"


NSMAP={'cac':XMLNamespaces.cac, 'cbc':XMLNamespaces.cbc, None:XMLNamespaces.empty}

XNS={   'cac':XMLNamespaces.cac,   
        'cbc':XMLNamespaces.cbc}

ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


class Peppol_To_Invoice(models.Model):
    _name = "peppol.toinvoice"
    _inherit = "peppol.topeppol"
    _description = "Module for converting invoice from Odoo to PEPPOL"

    def create_invoice(self):
        currency = self.getfield('account.move.currency_id,res.currency.name')
        invoice = etree.Element("Invoice", nsmap=NSMAP)

    #Invoice Instructions
        self.convert_field(invoice, 'Invoice', 'CustomizationID', text='urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0')
        self.convert_field(invoice, 'Invoice', 'ProfileID', text='urn:fdc:peppol.eu:2017:poacc:billing:04:1.0')
        self.convert_field(invoice, 'Invoice', 'ID', datamodule='account.move.name')
        self.convert_field(invoice, 'Invoice', 'IssueDate', datamodule='account.move.invoice_date')
        self.convert_field(invoice, 'Invoice', 'DueDate', datamodule='account.move.invoice_date_due')
        self.convert_field(invoice, 'Invoice', 'InvoiceTypeCode', text='380') #Might be account.move.move_type?
        #Not handled: Note: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-Note/
        #Not handled: TaxPointDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-TaxPointDate/
        self.convert_field(invoice, 'Invoice', 'DocumentCurrencyCode', datamodule='account.move.currency_id,res.currency.name')
        #Not handled: TaxCurrencyCode: Does this exist? Maybe in the account.move.line? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-TaxCurrencyCode/
        #Not handled: AccountingCost: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cbc-AccountingCost/
        self.convert_field(invoice, 'Invoice', 'BuyerReference', text='abs1234')

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
        self.convert_party(invoice, 'Invoice/cac:AccountingSupplierParty', 'account.move.company_id,res.company')
        """
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party', 'EndpointID', datamodule='account.move.company_id,res.company.vat', attri='schemeID:9955') #TODO: No error check here! Assumed to be swedish VAT number!
        #Not handled: AccountingSupplierParty/Party/PartyIdentification/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyIdentification/
        #Not handled: AccountingSupplierParty/Party/PartyName/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyName/cbc-Name/
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress', 'StreetName', text=self.get_company_street('account.move.company_id,res.company.street')[0])
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress', 'AdditionalStreetName', datamodule='account.move.company_id,res.company.street2')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress', 'CityName', datamodule='account.move.company_id,res.company.city')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress', 'PostalZone', datamodule='account.move.company_id,res.company.zip')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress', 'CountrySubentity', datamodule='account.move.company_id,res.company.state_id,res.country.state.name')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:AddressLine', 'Line', text=self.get_company_street('account.move.company_id,res.company.street')[1])
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country', 'IdentificationCode', datamodule='account.move.company_id,res.company.country_id,res.country.code')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme', 'CompanyID', datamodule='account.move.company_id,res.company.vat')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:TaxScheme', 'ID', text='VAT')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity', 'RegistrationName', datamodule='account.move.company_id,res.company.name')
        #Not Handled: AccountingSupplierParty/Party/PartyLegalEntity/CompanyID: Might be Organisation number. Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyID/
        #Not Handled: AccountingSupplierParty/Party/PartyLegalEntity/CompanyLegalForm: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyLegalForm/
        #Not Handled: AccountingSupplierParty/Party/Contact/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingSupplierParty/cac-Party/cac-Contact/cbc-Name/
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:Contact', 'Telephone', datamodule='account.move.company_id,res.company.phone')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:Contact', 'ElectronicMail', datamodule='account.move.company_id,res.company.email')        
        """
    #Accounting Customer Party Instructions
        self.convert_party(invoice, 'Invoice/cac:AccountingCustomerParty', 'account.move.partner_id,res.partner')
        """
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party', 'EndpointID', datamodule='account.move.partner_id,res.partner.vat', attri='schemeID:9955')#TODO: No error check here! Assumed to be swedish VAT number!
        #Not handled: AccountingCustomerParty/Party/PartyIdentification/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingCustomerParty/cac-Party/cac-PartyIdentification/
        #Not handled: AccountingCustomerParty/Party/PartyName/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingCustomerParty/cac-Party/cac-PartyName/
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress', 'StreetName', text=self.get_company_street('account.move.partner_id,res.partner.street')[0])
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress', 'AdditionalStreetName', datamodule='account.move.partner_id,res.partner.street2')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress', 'CityName', datamodule='account.move.partner_id,res.partner.city')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress', 'PostalZone', datamodule='account.move.partner_id,res.partner.zip')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress', 'CountrySubentity', datamodule='account.move.partner_id,res.partner.state_id,res.country.state.name')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:AddressLine', 'Line', text=self.get_company_street('account.move.partner_id,res.partner.street')[1])
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:Country', 'IdentificationCode', datamodule='account.move.partner_id,res.partner.country_id,res.country.code')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme', 'CompanyID', datamodule='account.move.partner_id,res.partner.vat')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cac:TaxScheme', 'ID', text='VAT')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity', 'RegistrationName', datamodule='account.move.partner_id,res.partner.name')
        #Not Handled: AccountingCustomerParty/Party/PartyLegalEntity/CompanyID: Might be Organisation number. Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingCustomerParty/cac-Party/cac-PartyLegalEntity/cbc-CompanyID/
        #Not Handled: AccountingCustomerParty/Party/Contact/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-AccountingCustomerParty/cac-Party/cac-Contact/cbc-Name/
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:Contact', 'Telephone', datamodule='account.move.partner_id,res.partner.phone')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:Contact', 'ElectronicMail', datamodule='account.move.partner_id,res.partner.email')        
        """

    #PayeeParty, is this even possible in Odoo?
    #TaxRepresentativeParty, is this even possible in Odoo?

    #Delivery, is this even possible in Odoo?
        #Not Handled: Delivery/ActualDeliveryDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-Delivery/cbc-ActualDeliveryDate/
        #Not Handled: Delivery/DeliveryLocation/ID: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-Delivery/cac-DeliveryLocation/cbc-ID/
        self.convert_address(invoice, 'Invoice/cac:Delivery/cac:DeliveryLocation', 'account.move.partner_shipping_id,res.partner') #THIS IS NOT CURRENT WORKING. WHY?
        #Not Handled: Delivery/DeliveryParty/PartyName/Name: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-Delivery/cac-DeliveryParty/cac-PartyName/cbc-Name/

    #PaymentMeans, these seem important but can't find them in Odoo.

    #PaymentTerms
        self.convert_field(invoice, 'Invoice/cac:PaymentTerms','Note', datamodule='account.move.narration')

    #AllowanceCharge, is this even possible in Odoo?

    #Tax Total Instructions
        self.convert_field(invoice, 'Invoice/cac:TaxTotal', 'TaxAmount', datamodule='account.move.amount_tax', attri='currencyID:'+currency)

        for vat_rate in self.get_all_different_vat_rates():
            new_tax_subtotal = etree.Element(QName(NSMAP['cac'], 'TaxSubtotal'), nsmap=NSMAP)

            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal', 'TaxableAmount', text=self.get_taxable_amount_for_vat_rate(vat_rate[0]), attri='currencyID:'+currency)
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal', 'TaxAmount', text=self.get_tax_amount_for_vat_rate(vat_rate[0]), attri='currencyID:'+currency)
            
            #The below lines should be set based on the account-move.line.tax_ids. However, in it you can only find the information one wants in the 'name', which is in swedish. Is there a solution to this?
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal/cac:TaxCategory', 'ID', text=vat_rate[1])
            #TaxExemptionReasonCode
            #TaxExemptionReason

            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal/cac:TaxCategory', 'Percent', text=vat_rate[0])
            self.convert_field(new_tax_subtotal, 'cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme', 'ID', text='VAT')

            #TODO: Make this skip if this vat is 'false' for some reason.
            #if XPATH

            invoice.xpath('/Invoice/cac:TaxTotal', namespaces=XNS)[0].append(new_tax_subtotal)

    #Legal Monetary Total
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'LineExtensionAmount', text=str(self.get_line_extension_amount()), attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'TaxExclusiveAmount', datamodule='account.move.amount_untaxed', attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'TaxInclusiveAmount', datamodule='account.move.amount_total', attri='currencyID:'+currency)
        #Not Handled: LegalMonetaryTotal/AllowanceTotalAmount: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-LegalMonetaryTotal/cbc-AllowanceTotalAmount/
        #Not Handled: LegalMonetaryTotal/ChargeTotalAmount: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-LegalMonetaryTotal/cbc-ChargeTotalAmount/
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'PrepaidAmount', text=self.get_prepaid_amount(), attri='currencyID:'+currency)
        #Not Handled: LegalMonetaryTotal/PayableRoundingAmount: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-LegalMonetaryTotal/cbc-PayableRoundingAmount/
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'PayableAmount', datamodule='account.move.amount_residual', attri='currencyID:'+currency)
    
    #Invoice Line
        #TODO: Instead of using 'recordset' here, it aught to be possible to enter the path to the wanted datafield using only the datamodule and the current id from 'line'.
        n = 0
        for line in self['invoice_line_ids']:
            n += 1
            new_line = etree.Element(QName(NSMAP['cac'], 'InvoiceLine'), nsmap=NSMAP)

            #_logger.warning(f"{(self.getfield('account.move.line.display_type', line))=}")
            if self.getfield('account.move.line.display_type', line) != False:
                continue
                #pass
                #self.convert_field(new_line, 'cac:InvoiceLine', 'ID', text=str(n), recordset=line)
                #self.convert_field(new_line, 'cac:InvoiceLine/cac:Item', 'Name', datamodule='account.move.line.name', recordset=line)
            #else:
            self.convert_field(new_line, 'cac:InvoiceLine', 'ID', text=str(n), recordset=line)
            #Not Handled: InvoiceLine/Note: This does not exist built into the line, but as a seperate line. https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/
            self.convert_field(new_line, 'cac:InvoiceLine', 'InvoicedQuantity', datamodule='account.move.line.quantity', attri='unitCode:C62', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine', 'LineExtensionAmount', text=self.get_line_extension_amount_per_line(line), attri='currencyID:'+currency)
            #Not Handled: InvoiceLine/AccountingCost: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cbc-AccountingCost/
            #Not Handled: InvoiceLine/InvoicePeriod/StartDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-InvoicePeriod/cbc-StartDate/
            #Not Handled: InvoiceLine/InvoicePeriod/EndDate: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-InvoicePeriod/
            #Not Handled: InvoiceLine/OrderLineReference/LineID: Needs an Order Referance to be handled. https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-OrderLineReference/cbc-LineID/
            #Not Handled: InvoiceLine/DocumentReference: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-DocumentReference/
            #Not Handled: InvoiceLine/AllowanceCharge: Does this exist? https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-InvoiceLine/cac-AllowanceCharge/
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item', 'Description', datamodule='account.move.line.name', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item', 'Name', datamodule='account.move.line.product_id,product.product.name', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory', 'ID', text=self.translate_tax_category_to_peppol(self.getfield('account.move.line.tax_ids,account.tax.name', line)))
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory', 'Percent', datamodule='account.move.line.tax_ids,account.tax.amount', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory/cac:TaxScheme', 'ID', text='VAT', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Price', 'PriceAmount', text=(self.getfield('account.move.line.price_subtotal', line) / self.getfield('account.move.line.quantity', line)), attri='currencyID:'+currency, recordset=line)

            invoice.append(new_line)

    #Cleanup
        if self.remove_empty_elements(invoice) is None:
            return None  

        return invoice

#Helper Functions
    def get_line_extension_amount(self):
        amount = 0
        #_logger.error(f"{self['invoice_line_ids']=}")
        for line in self['invoice_line_ids']:
            #self.getfield('account.move.line.price_subtotal', line)
            amount += self.getfield('account.move.line.price_subtotal', line)
        #_logger.error(f"Found {amount=}")
        return amount

    def get_prepaid_amount(self):
        prepaid_amount = self.getfield('account.move.amount_total') - self.getfield('account.move.amount_residual')
        if prepaid_amount == 0:
            prepaid_amount = None
        return prepaid_amount
    
    def get_all_different_vat_rates(self):
        unique_vats = set()
        _logger.error(f"{self['invoice_line_ids']=}")
        for line in self['invoice_line_ids']:
            unique_vats.add((   self.getfield('account.move.line.tax_ids,account.tax.amount', line), 
                                self.translate_tax_category_to_peppol(self.getfield('account.move.line.tax_ids,account.tax.name', line))))
        _logger.error(f"{unique_vats=}")        
        return unique_vats

    def get_taxable_amount_for_vat_rate(self, vat_rate):
        taxable_amount = 0
        for line in self['invoice_line_ids']:
            if self.getfield('account.move.line.tax_ids,account.tax.amount', line) == vat_rate:
                taxable_amount += self.getfield('account.move.line.price_subtotal', line)
        return taxable_amount

    def get_tax_amount_for_vat_rate(self, vat_rate):
        tax_amount = 0
        for line in self['invoice_line_ids']:
            if self.getfield('account.move.line.tax_ids,account.tax.amount', line) == vat_rate:
                tax_amount += (self.getfield('account.move.line.price_total', line) - self.getfield('account.move.line.price_subtotal', line) ) 
        return tax_amount

    def get_line_extension_amount_per_line(self, line):
        #amount = self.getfield('account.move.line.price_subtotal', line)
        #if amount is None:
        #    return None
        #if self.is_vat_inclusive(self.getfield('account.move.line.tax_ids,account.tax.name', line)):
        amount = self.getfield('account.move.line.price_subtotal', line)
        return amount

    def is_vat_inclusive(self, type):
        try:
            if type[-1] == 'i' and len(type) > 1:
                return True
        except:
            pass
        return False