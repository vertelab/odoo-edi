{
    'name': 'EDI: Extend Invoice Import for Incoming Invoices via Mail',
    'version': '14.0.0.0.0',
    'summary': 'Extend Invoice Import for Incoming Invoices via Mail',
    'category': 'Accounting',
    'description': """
        Extends account_invoice_import_simple_pdf for incoming invoices by mail
    """,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-edi/account_invoice_import_simple_mail',
    'license': 'AGPL-3',
    'repository': 'https://github.com/vertelab/odoo-edi',
    'depends': ['account_invoice_import_simple_pdf', 'account'],
    "data": [
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
