# Stock Move model extension will be implemented here.
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_reference_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice Reference",
        readonly=True,
        copy=False,
        index=True,
    )
