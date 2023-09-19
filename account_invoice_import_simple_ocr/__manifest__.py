{
    'name': 'EDI: OCR Account Invoice Import',
    'version': '14.0.0.0.0',
    'summary': 'OCR Account Invoice Import.',
    'category': 'Accounting',
    'description': """
        Extends (OCA) module account_invoice_import_simple_pdf in edi with OCR using tesseract library
    """,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-edi/account_invoice_import_simple_ocr',
    'license': 'AGPL-3',
    'repository': 'https://github.com/vertelab/odoo-edi',
    'depends': ['account_invoice_import_simple_pdf', ],
    "data": [
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
