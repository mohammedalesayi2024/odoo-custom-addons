{
    "name": "Receipt Book Management",
    "version": "19.0.1.0",
    "summary": "Manage manual receipt books for salespersons",
    "description": """
Receipt Book Management

Features:
- Manage receipt books
- Assign receipt books to salespersons
- Automatic receipt numbering
- Receipt exceptions
- Integration with Customer Payments
""",
    "author": "Mohammed alesayi",
    "license": "LGPL-3",
    "category": "Accounting",
    "website": "",
    "depends": [
        "account",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/receipt_book_views.xml",
        "views/account_payment_views.xml",
        "views/receipt_exception_views.xml",
        "wizard/receipt_exception_wizard_views.xml",
        "wizard/receipt_delayed_wizard_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "receipt_book_management/static/src/scss/receipt_book.scss",
            "receipt_book_management/static/src/js/receipt_exception_list.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
