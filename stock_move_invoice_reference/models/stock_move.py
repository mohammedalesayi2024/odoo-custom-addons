# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_reference_id = fields.Many2one(
        "account.move",
        string="Invoice Reference",
        copy=False,
        index=True,
    )
