{
    "name": "Receipt Book Management - Multiple Books",
    "version": "19.0.1.1",
    "summary": "Allow a salesperson to have multiple receipt books with separate number ranges",
    "description": """
Receipt Book Management - Multiple Books

Extension for the original Receipt Book Management module.

Features:
- A salesperson can have multiple receipt books at the same time.
- Prevents overlapping receipt-number ranges for the same salesperson and company.
- Allows selecting the required receipt book on customer payments.
- Each receipt book keeps its own next receipt number.
- Keeps the original receipt exception and delayed-receipt workflow.
""",
    "author": "Mohammed alesayi",
    "license": "LGPL-3",
    "category": "Accounting",
    "website": "",
    "depends": [
        "receipt_book_management",
    ],
    "data": [
        "views/account_payment_views_multi.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
