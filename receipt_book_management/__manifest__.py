{
    "name": "Receipt Book Management",
    "version": "19.0.1.0.0",
    "summary": "Manage Manual Receipt Books for Salespersons",
    "description": """
Receipt Book Management

Features:
- Assign receipt books to salespersons
- Automatic manual receipt numbering
- Remaining receipt tracking
- Near end warning
- Finished receipt books
    """,
    "author": "Mohammed",
    "website": "",
    "license": "LGPL-3",
    "category": "Accounting",
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/receipt_book_views.xml",
        "views/res_users_views.xml",
        "views/account_payment_views.xml",
        'views/receipt_salesperson_views.xml',
    ],
    "installable": True,
    "application": True,
}
