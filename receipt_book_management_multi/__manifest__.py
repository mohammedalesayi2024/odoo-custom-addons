{
    "name": "Receipt Book Management - Multiple Books",
    "version": "19.0.1.1",
    "summary": "Allow salespersons to have multiple receipt books with different number ranges",
    "description": """
Receipt Book Management - Multiple Books

Extension for Receipt Book Management.

Features:
- A salesperson can have multiple receipt books at the same time.
- Receipt book can be selected manually on customer payments.
- Each receipt book keeps its own numbering sequence.
- Prevents overlapping receipt-number ranges for the same salesperson/company.
- Keeps the original receipt-book workflows, exceptions and numbering logic.
""",
    "author": "Mohammed alesayi",
    "license": "LGPL-3",
    "category": "Accounting",
    "depends": [
        "receipt_book_management",
    ],
    "data": [
        "views/account_payment_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}