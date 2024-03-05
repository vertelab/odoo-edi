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
        sudo apt install build-essential
        sudo apt install libpoppler-cpp-dev
        sudo apt install pkg-config python3-dev
        sudo pip3 install PyMuPDF
        sudo pip3 install pytesseract
        sudo pip3 install pdftotext

    """,
    "external_dependencies": {
        "python": ["PyMuPDF", "pytesseract", "pdftotext"],
        "deb": ["tesseract-ocr", "poppler-utils", "build-essential", "libpoppler-cpp-dev", "pkg-config python3-dev"],
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
