# -*- coding: utf-8 -*-

{
    "name": "POS Printer Tags",
    "version": "19.0.1.0.0",
    "summary": "Route POS kitchen printers using Product Tags.",
    "description": """
POS Printer Tags
================

This module extends the Point of Sale printer configuration by allowing
kitchen printers to filter products using Product Tags in addition to
Product Categories.

Main Features
-------------
* Add Printed Product Tags to POS Printers.
* Route kitchen orders based on Product Tags.
* Fully compatible with the standard POS printer workflow.
* No modification to Odoo core files.

    """,
    "author": "Mohammed",
    "website": "",
    "license": "LGPL-3",
    "category": "Point of Sale",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "views/pos_printer_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_printer_tags/static/src/js/*.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}