{
    'name': 'EDI: Ocr with Image Enhancement',
    'version': '14.0.0.0.0',
    'summary': 'OCR Account Invoice Import with Image Enhancement.',
    'category': 'Accounting',
    'description': """
        Extends (OCA) module account_invoice_import_simple_pdf and account_invoice_import_simple_ocr in EDI

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
    'external_dependencies': {
        'python': ['PyMuPDF', 'pytesseract', 'pdftotext'],
        'deb': ['tesseract-ocr', 'poppler-utils', 'build-essential', 'libpoppler-cpp-dev', 'pkg-config', 'python3-dev'],
    },
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-edi/hassan-14-enhanced_ocr',
    'license': 'AGPL-3',
    'repository': 'https://github.com/vertelab/odoo-edi',
    'depends': [
        'account_invoice_import_simple_pdf',
        'account_invoice_import_simple_ocr'
    ],
    'data': [
        'views/account_invoice_import_image_correction.xml',
        'views/account_invoice_import_image_correction_res_partner.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
