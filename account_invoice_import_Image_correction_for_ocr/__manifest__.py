{
    'name': 'Pre Ocr Image Correction',
    'version': '14.0.1.0.0',
    'summary': 'OCR Account Invoice Import pre image correction.',
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
        "deb": ["tesseract-ocr" ,"poppler-utils", "build-essential", "libpoppler-cpp-dev", "pkg-config python3-dev"],
    },
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-edi/account_invoice_import_simple_ocr',
    'license': 'AGPL-3',
    'repository': 'https://github.com/vertelab/odoo-edi',
    'depends': ['account_invoice_import_simple_pdf',],
    "data": [
        'views/custom_image_correction.xml',
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
