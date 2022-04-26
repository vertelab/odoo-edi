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
    _inherit = ["peppol.topeppol"]
    _description = "Module for converting invoice from Odoo to PEPPOL"


    def create_invoice(self):
        currency = self.getfield('account.move.currency_id,res.currency.name')
        invoice = etree.Element("Invoice", nsmap=NSMAP)

        _logger.warning("Running Create_Invoice!")

        #I am Fake!
        self.convert_field(invoice, 'Invoice', 'NotReal', datamodule='account.move.Idontexist')

        #Invoice Instructions
        self.convert_field(invoice, 'Invoice', 'CustomizationID', text='urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0')
        self.convert_field(invoice, 'Invoice', 'ProfileID', text='urn:fdc:peppol.eu:2017:poacc:billing:04:1.0')
        self.convert_field(invoice, 'Invoice', 'ID', datamodule='account.move.name')
        self.convert_field(invoice, 'Invoice', 'IssueDate', datamodule='account.move.invoice_date')
        self.convert_field(invoice, 'Invoice', 'DueDate', datamodule='account.move.invoice_date_due')
        self.convert_field(invoice, 'Invoice', 'DocumentCurrencyCode', datamodule='account.move.currency_id,res.currency.name')
        self.convert_field(invoice, 'Invoice', 'InvoiceTypeCode', text='380')
        self.convert_field(invoice, 'Invoice', 'BuyerReference', text='abs1234')

        #Accounting Supplier Party Instructions
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party', 'EndpointID', datamodule='account.move.company_id,res.company.vat', attri='schemeID:9955') #TODO: No error check here! Assumed to be swedish VAT number!
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country', 'IdentificationCode', datamodule='account.move.company_id,res.company.country_id,res.country.code')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme', 'CompanyID', text='SE123456789012')
        self.convert_field(invoice, 'Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:TaxScheme', 'ID', text='VAT')

        #Accounting Customer Party Instructions
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party', 'EndpointID', datamodule='account.move.partner_id,res.partner.vat', attri='schemeID:9955')#TODO: No error check here! Assumed to be swedish VAT number!
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:Country', 'IdentificationCode', datamodule='account.move.partner_id,res.partner.country_id,res.country.code')
        self.convert_field(invoice, 'Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity', 'RegistrationName', datamodule='account.move.partner_id,res.partner.name')

        #Tax Total Instructions
        self.convert_field(invoice, 'Invoice/cac:TaxTotal', 'TaxAmount', datamodule='account.move.amount_tax', attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:TaxTotal/cac:TaxSubtotal', 'TaxableAmount', datamodule='account.move.amount_total', attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:TaxTotal/cac:TaxSubtotal', 'TaxAmount', datamodule='account.move.amount_tax', attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory', 'ID', text='S')
        self.convert_field(invoice, 'Invoice/cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory', 'Percent', text='25')
        self.convert_field(invoice, 'Invoice/cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme', 'ID', text='VAT')

        #Legal Monetary Total
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'LineExtensionAmount', text=str(self.get_line_extension_amount()), attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'TaxExclusiveAmount', datamodule='account.move.amount_untaxed', attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'TaxInclusiveAmount', datamodule='account.move.amount_total', attri='currencyID:'+currency)
        self.convert_field(invoice, 'Invoice/cac:LegalMonetaryTotal', 'PayableAmount', datamodule='account.move.amount_residual', attri='currencyID:'+currency)

        #Invoice Line
        #TODO: Instead of using 'recordset' here, it aught to be possible to enter the path to the wanted datafield using only the datamodule and the current id from 'line'.
        n = 0
        for line in self['invoice_line_ids']:
            n += 1

            new_line = etree.Element(QName(NSMAP['cac'], 'InvoiceLine'), nsmap=NSMAP)

            self.convert_field(new_line, 'cac:InvoiceLine', 'ID', text=str(n), recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine', 'InvoicedQuantity', datamodule='account.move.line.quantity', attri='unitCode:C62', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine', 'LineExtensionAmount', datamodule='account.move.line.price_subtotal', attri='currencyID:'+currency, recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item', 'Name', datamodule='account.move.line.name', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory', 'ID', text='S', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory', 'Percent', datamodule='account.move.line.tax_ids,account.tax.amount', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory/cac:TaxScheme', 'ID', text='VAT', recordset=line)
            self.convert_field(new_line, 'cac:InvoiceLine/cac:Price', 'PriceAmount', datamodule='account.move.line.price_unit', attri='currencyID:'+currency, recordset=line)

            invoice.append(new_line)

        return invoice


    def get_line_extension_amount(self):
        amount = 0
        for line in self['invoice_line_ids']:
            amount += self.getfield('account.move.line.price_subtotal', line)

        return amount