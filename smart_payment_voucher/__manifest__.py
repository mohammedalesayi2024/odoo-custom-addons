{
    "name": "Smart Payment Voucher",
    "version": "19.0.1.0.1",
    "category": "Accounting",
    "summary": "Professional Receipt and Payment Voucher Reports",
    "description": """
Smart Payment Voucher

Features:
- Receipt Voucher
- Payment Voucher
- Company Stamp
- Company Signature
- QR Code Support
- Multi Company Support
- Arabic & English Layout
    """,
    "author": "Mohammed",
    "website": "",
    "license": "LGPL-3",
    "depends": [
        "account",
    ],
    "data": [

        "views/res_company_views.xml",
        "views/account_payment_views.xml",

        "reports/receipt_voucher.xml",
        "reports/payment_voucher.xml",
        "reports/receipt_template.xml",
        "reports/payment_template.xml",
    ],
    "installable": True,
    "application": True,
}