{
    "name": "Receipt Book Management - Multiple Books",
    "version": "19.0.0.1",
    "summary": "Manage multiple receipt books per salesperson",
    "description": """
Standalone Receipt Book Management - Multiple Books

Features:
- Manage receipt books independently from the original Receipt Book Management module.
- Assign multiple receipt books to the same salesperson.
- Prevent overlapping number ranges for the same salesperson/company.
- Automatic receipt numbering.
- Select the required receipt book on customer payments.
- Receipt exceptions and delayed/skipped receipt workflows.
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
            "receipt_book_management_multi/static/src/scss/receipt_book.scss",
            "receipt_book_management_multi/static/src/js/receipt_exception_list.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
