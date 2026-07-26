{
    "name": "Stock Move Invoice Reference",
    "version": "19.0.1.0.0",
    "summary": "Display invoice reference on stock moves.",
    "description": """
Stock Move Invoice Reference

Adds an invoice reference to stock moves, allowing users to:
- View the related invoice.
- Open the invoice directly.
- Search and filter stock moves by invoice reference.

Supported Documents:
- Customer Invoices
- Vendor Bills
- Customer Credit Notes
- Vendor Credit Notes
""",
    "author": "Mohammed_alesayi7",
    "website": "",
    "category": "Inventory/Reporting",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "account",
        "sale_management",
        "purchase",
    ],
    "data": [
        "views/stock_move_line_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
