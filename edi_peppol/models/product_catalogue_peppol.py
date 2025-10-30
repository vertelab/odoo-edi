from odoo import models, fields

class ProductCataloguePeppol(models.Model):
    _name = "product.catalogue.peppol"
    _description = "PEPPOL Product Catalogue"

    name = fields.Char(string="Catalogue Name", required=True)
    line_ids = fields.One2many(
        'product.catalogue.peppol.line',
        'catalogue_id',
        string="Catalogue Lines"
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')],
        default='pending', string="State")

    # Additional catalogue-level info
    referenced_contract = fields.Char(string="Referenced Contract")
    agreement_id = fields.Many2one('agreement', string="Agreement")

    validity_period_start_date = fields.Datetime(string="Validity Start")
    validity_period_end_date = fields.Datetime(string="Validity End")

    # Provider info
    provider_party = fields.Many2one("res.partner", string="Provider Party")
    provider_contact = fields.Many2one("res.partner", string="Provider Contact")
    provider_postal_address = fields.Many2one("res.partner", string="Provider Postal Address")
    provider_party_legal_entity = fields.Many2one("res.partner", string="Provider Legal Entity")

    # Receiver info
    receiver_party = fields.Many2one("res.partner", string="Receiver Party")
    receiver_contact = fields.Many2one("res.partner", string="Receiver Contact")
    receiver_postal_address = fields.Many2one("res.partner", string="Receiver Postal Address")
    receiver_party_legal_entity = fields.Many2one("res.partner", string="Receiver Legal Entity")

    # Seller info
    seller_supplier_party = fields.Many2one("res.partner", string="Seller Supplier Party")
    seller_supplier_contact = fields.Many2one("res.partner", string="Seller Contact")
    seller_supplier_postal_address = fields.Many2one("res.partner", string="Seller Postal Address")
    seller_supplier_party_legal_entity = fields.Many2one("res.partner", string="Seller Legal Entity")

    # Contractor/Customer info
    contractor_customer_party = fields.Many2one("res.partner", string="Contractor/Customer Party")
    contractor_customer_contact = fields.Many2one("res.partner", string="Contractor/Customer Contact")
    contractor_customer_postal_address = fields.Many2one("res.partner", string="Contractor/Customer Postal Address")
    contractor_customer_party_legal_entity = fields.Many2one("res.partner", string="Contractor/Customer Legal Entity")

    edi_message_id = fields.Many2one('edi.message', string="EDI Message")

    product_data = fields.Text(string="Product Data")

    def action_accept_catalogue(self):
        for line in self.line_ids:
            if not line.product_id and line.json_data:
                json_data = eval(line.json_data)
                catalogue_item_data = self.edi_message_id._get_catalogue_item(item=json_data.get('Item'))
                line.product_id = self.env['product.product'].create(catalogue_item_data).id
        self.state = 'accepted'

    def action_decline_catalogue(self):
        self.state = 'declined'

    
    
class ProductCataloguePeppolLine(models.Model):
    _name = "product.catalogue.peppol.line"
    _description = "PEPPOL Product Catalogue Line"

    name = fields.Char(string="Line Name", required=True)
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product Template",
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product",
    )
    catalogue_id = fields.Many2one(
        'product.catalogue.peppol',
        string="Catalogue Reference",
        ondelete="cascade"
    )
    action_code = fields.Char(string="Action Code")
    content_unit_quantity = fields.Char(string="Content Unit Qty")
    min_order_quantity = fields.Char(string="Mini Order Qty")
    min_order_quantity_unit_code = fields.Char(string="Mini Order Qty Unit Code")

    sellers_item_identification = fields.Char(string='Seller’s Item Identification')
    manufacturers_item_identification = fields.Char(string='Manufacturer’s Item Identification')
    item_specification_document_ref = fields.Char(string='Item Specification Document Reference')

    standard_item_identification_code = fields.Char(string='Standard Item Identification Code')
    standard_item_identification = fields.Char(string='Standard Item Identification')
    json_data = fields.Char(string='JSON Data')


