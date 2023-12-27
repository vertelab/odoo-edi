{
    'name': 'EDI: OCR Account Invoice Import',
    'version': '14.0.0.0.0',
    'summary': 'OCR Account Invoice Import.',
    'category': 'Accounting',
    'description': """
        Extends (OCA) module account_invoice_import_simple_pdf in edi

        Guide of tesseract
        sudo apt install poppler-utils
        sudo apt install tesseract-ocr
        sudo pip3 install PyMuPDF
        sudo pip3 install pytesseract

    """,
    "external_dependencies": {
        "python": ["PyMuPDF", "pytesseract"],
        "deb": ["tesseract-ocr" ,"poppler-utils"],
    },
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
