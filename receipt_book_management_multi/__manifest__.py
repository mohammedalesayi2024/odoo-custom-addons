{
    "name": "Receipt Book Management - Multiple Books",
    "version": "19.0.1.1",
    "summary": "Manage manual receipt books and allow multiple books per salesperson",
    "description": """
Receipt Book Management - Multiple Books

Features:
- Manage receipt books
- Assign multiple receipt books to the same salesperson
- Automatic receipt numbering
- Receipt exceptions
- Integration with Customer Payments
- Separate receipt-number ranges per receipt book
- Prevent overlapping receipt-number ranges for the same salesperson and company
""",
    "author": "Mohammed alesayi",
    "license": "LGPL-3",
    "category": "Accounting",
    "website": "",
    "depends": [
        "account",
        "receipt_book_management",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/receipt_book_views.xml",
        "views/account_payment_views.xml",
        "views/account_payment_views_multi.xml",
        "views/receipt_exception_views.xml",
        "wizard/receipt_exception_wizard_views.xml",
        "wizard/receipt_delayed_wizard_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "receipt_book_management_multi/static/src/scss/receipt_book.scss",
            "receipt_book_management_multi/static/src/js/receipt_exception_list.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
