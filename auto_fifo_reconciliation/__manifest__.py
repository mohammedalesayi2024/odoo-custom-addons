{
    "name": "Auto FIFO Reconciliation",
    "version": "19.0.1.0.3",
    "category": "Accounting",
    "summary": "Automatically reconcile customer and vendor payments using FIFO.",
    "description": """
Auto FIFO Reconciliation

This module automatically reconciles customer and vendor payments
with the oldest outstanding accounting entries using the FIFO method.

Features:
- Automatic reconciliation after posting payments.
- Supports customer payments.
- Supports vendor payments.
- Supports manual journal entries.
- FIFO allocation by transaction date.
- FIFO allocation by due date.
- Per-partner configuration.
- Fully integrated with Odoo Accounting.

Compatible with Odoo 19.
""",
    "author": "Mohammed",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/security.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}