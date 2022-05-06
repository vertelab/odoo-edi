import logging
from odoo import models, api, _, fields

from lxml import etree, objectify
from lxml.etree import Element, SubElement, QName, tostring

_logger = logging.getLogger(__name__)


class NSMAPS:
    cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    empty="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

    NSMAP={'cac':cac, 'cbc':cbc, 'ubl':empty}

    XNS={'cac':cac,   
         'cbc':cbc,
         'ubl':empty}

    ns = {k:'{' + v + '}' for k,v in NSMAP.items()}


class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.toinvoice", "peppol.toorder", "peppol.frominvoice"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."


    def to_peppol_button(self):
        self.to_peppol()
        return None

    def from_peppol_button(self):
        return self.from_peppol()
  
    def to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())
        #self.env['peppol.toinvoice'].create_invoice())
        #_logger.warning("XML has ID: " + tree.xpath('/Invoice/cbc:ID/text()', namespaces=XNS)[0])
        #tree = etree.ElementTree(self.create_order())

        _logger.error(self.invoice_line_ids)
        
        tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

        #_logger.error(inspect.currentframe().f_code.co_name + ": " + "NO VALIDATION IS DONE!")
        #_logger.warning("Starting validation attemps")

        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml')

    def from_peppol(self):
        tree = self.parse_xml('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        #with open('/usr/share/odoo-edi/edi_peppol/demo/output.xml') as f:
        #    xml = f.read()
        #_logger.warning(f"{xml=}")
        #    tree = objectify.parse(f)
        #tree = objectify.parse('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        #tree = self.parseXML('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        #root = objectify.Element("root")
        #b = objectify.SubElement(root, "b")
        #_logger.warning(root.b[0].tag)

        #_logger.warning(isinstance(tree.getroot(), objectify.ObjectifiedElement)) #TODO: Make this into a actual error check, as this should always be 'True'!

        #_logger.warning(f"{tree=}")

        if tree is None:
            return None

        #return self.user_choice_window()

        tmp = self.import_invoice(tree)

        #_logger.error(self.invoice_line_ids)

        return tmp





    def parseXML(self, xmlFile):
        """"""
        #with open(xmlFile) as f:
        #    xml = f.read()
            
        #root = objectify.fromstring(xml)
        xml = '''<Invoice xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:04:1.0</cbc:ProfileID>
  <cbc:ID>INV/2022/04/0002</cbc:ID>
  <cbc:IssueDate>2022-04-29</cbc:IssueDate>
  <cbc:DueDate>2022-05-31</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>SEK</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>abs1234</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="9955">SE810354746201</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>Storgatan 12</cbc:StreetName>
        <cbc:CityName>Ängelholms kommun</cbc:CityName>
        <cbc:PostalZone>262 64</cbc:PostalZone>
        <cac:Country>
          <cbc:IdentificationCode>SE</cbc:IdentificationCode>
        </cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>SE810354746201</cbc:CompanyID>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>SE Company</cbc:RegistrationName>
      </cac:PartyLegalEntity>
      <cac:Contact>
        <cbc:Telephone>+46 70 123 45 67</cbc:Telephone>
        <cbc:ElectronicMail>info@company.seexample.com</cbc:ElectronicMail>
      </cac:Contact>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="9955">SE556936370701</cbc:EndpointID>
      <cac:PostalAddress>
        <cbc:StreetName>250 Executive Park Blvd</cbc:StreetName>
        <cbc:CityName>Mjölby</cbc:CityName>
        <cbc:PostalZone>94134</cbc:PostalZone>
        <cbc:CountrySubentity>Östergötlands län</cbc:CountrySubentity>
        <cac:AddressLine>
          <cbc:Line>Suite 3400</cbc:Line>
        </cac:AddressLine>
        <cac:Country>
          <cbc:IdentificationCode>SE</cbc:IdentificationCode>
        </cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>SE556936370701</cbc:CompanyID>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>YourCompany</cbc:RegistrationName>
      </cac:PartyLegalEntity>
      <cac:Contact>
        <cbc:Telephone>+1 (650) 555-0111</cbc:Telephone>
        <cbc:ElectronicMail>info@yourcompany.com</cbc:ElectronicMail>
      </cac:Contact>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:Delivery>
    <cac:DeliveryLocation>
      <cac:Address>
        <cbc:StreetName>250 Executive Park Blvd</cbc:StreetName>
        <cbc:CityName>Mjölby</cbc:CityName>
        <cbc:PostalZone>94134</cbc:PostalZone>
        <cbc:CountrySubentity>Östergötlands län</cbc:CountrySubentity>
        <cac:AddressLine>
          <cbc:Line>Suite 3400</cbc:Line>
        </cac:AddressLine>
        <cac:Country>
          <cbc:IdentificationCode>SE</cbc:IdentificationCode>
        </cac:Country>
      </cac:Address>
    </cac:DeliveryLocation>
  </cac:Delivery>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="SEK">917.35</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="SEK">474.0</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="SEK">0.0</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>Z</cbc:ID>
        <cbc:Percent>0.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="SEK">3631.0</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="SEK">907.75</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>25.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="SEK">80.0</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="SEK">9.6</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>12.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="SEK">4185.0</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="SEK">4185.0</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="SEK">5102.35</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="SEK">5102.35</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="C62">2.0</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="SEK">3598.0</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>A REALLY LONG DESCRIPTION OF A LARGE TABLE. IT IS LONG AND TABLE-LIKE.</cbc:Description>
      <cbc:Name>Stort skrivbord</cbc:Name>
      <cac:SellersItemIdentification>
        <cbc:ID>E-COM09</cbc:ID>
      </cac:SellersItemIdentification>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>25.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="SEK">1799.0</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="C62">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>
  <cac:InvoiceLine>
    <cbc:ID>2</cbc:ID>
    <cbc:InvoicedQuantity unitCode="C62">6.0</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="SEK">474.0</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>[E-COM08] Förvaringslåda</cbc:Description>
      <cbc:Name>Förvaringslåda</cbc:Name>
      <cac:SellersItemIdentification>
        <cbc:ID>E-COM08</cbc:ID>
      </cac:SellersItemIdentification>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>Z</cbc:ID>
        <cbc:Percent>0.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="SEK">79.0</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="C62">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>
  <cac:InvoiceLine>
    <cbc:ID>3</cbc:ID>
    <cbc:InvoicedQuantity unitCode="C62">2.0</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="SEK">33.0</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>[E-COM12] Konferensstol (KONFIG) (Steel)</cbc:Description>
      <cbc:Name>Konferensstol (KONFIG)</cbc:Name>
      <cac:SellersItemIdentification>
        <cbc:ID>E-COM12</cbc:ID>
      </cac:SellersItemIdentification>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>25.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="SEK">16.5</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="C62">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>
  <cac:InvoiceLine>
    <cbc:ID>4</cbc:ID>
    <cbc:InvoicedQuantity unitCode="C62">2.0</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="SEK">80.0</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>[FURN_8888] Kontorslampa</cbc:Description>
      <cbc:Name>Kontorslampa</cbc:Name>
      <cac:SellersItemIdentification>
        <cbc:ID>FURN_8888</cbc:ID>
      </cac:SellersItemIdentification>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>S</cbc:ID>
        <cbc:Percent>12.0</cbc:Percent>
        <cac:TaxScheme>
          <cbc:ID>VAT</cbc:ID>
        </cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="SEK">40.0</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="C62">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>
</Invoice>
'''



        root = objectify.fromstring(xml)

        # returns attributes in element node as dict
        attrib = root.attrib
        
        

        # how to extract element data
        SupplierID = root[self.ns('cac') + 'AccountingSupplierParty']
        #uid = root.appointment.uid

        _logger.error(f"{SupplierID=}")

        # loop over elements and print their tags and text
        #for appt in root.getchildren():
        #    for e in appt.getchildren():
        #        _logger.warning("%s => %s" % (e.tag, e.text))
        
        # how to change an element's text
        #root.appointment.begin = "something else"
        #print(root.appointment.begin)
        
        # how to add a new element
        #root.appointment.new_element = "new data"
        
        # print the xml
        #obj_xml = etree.tostring(root, pretty_print=True)
        #print(obj_xml)
        
        # remove the py:pytype stuff
        #objectify.deannotate(root)
        #etree.cleanup_namespaces(root)
        #obj_xml = etree.tostring(root, pretty_print=True)
        #print(obj_xml)
        
        # save your xml
        #with open("new.xml", "w") as f:
        #    f.write(obj_xml)

        return root

    def ns(self, msg):
        return '{' + NSMAPS.NSMAP[msg] + '}'



    """
    def btn_show_dialog_box(self):
        text = "THIS IS MY SPECIAL MESSAGE!"
        query ='delete from display_dialog_box'
        self.env.cr.execute(query)
        value = self.env['display.dialog.box'].sudo().create({'text':text})
        return{
            'type':'ir.actions.act_window',
            'name':'Message',
            'res_model':'display.dialog.box',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'res_id':value.id                
        }

            "type": "ir.actions.act_window",
            "res_model": "res.currency",
            "views": [[False, "tree"], [False, "form"]],
            "target": "new",
            "domain": [("id", "=", "18")],     
    """
