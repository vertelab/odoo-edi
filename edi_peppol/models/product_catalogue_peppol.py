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

    # Additional catalogue-level info
    referenced_contract = fields.Char(string="Referenced Contract")

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
    seller_contact = fields.Many2one("res.partner", string="Seller Contact")
    seller_postal_address = fields.Many2one("res.partner", string="Seller Postal Address")
    seller_party_legal_entity = fields.Many2one("res.partner", string="Seller Legal Entity")

    # Contractor/Customer info
    contractor_customer_supplier_party = fields.Many2one("res.partner", string="Contractor/Customer Party")
    contractor_customer_contact = fields.Many2one("res.partner", string="Contractor/Customer Contact")
    contractor_customer_postal_address = fields.Many2one("res.partner", string="Contractor/Customer Postal Address")
    contractor_customer_party_legal_entity = fields.Many2one("res.partner", string="Contractor/Customer Legal Entity")

    
    
class ProductCataloguePeppolLine(models.Model):
    _name = "product.catalogue.peppol.line"
    _description = "PEPPOL Product Catalogue Line"

    name = fields.Char(string="Line Name", required=True)
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product Template",
        required=True
    )
    catalogue_id = fields.Many2one(
        'product.catalogue.peppol',
        string="Catalogue Reference",
        ondelete="cascade"
    )
