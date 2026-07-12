from odoo import fields, models


class ReceiptSalesperson(models.Model):
    _name = "receipt.salesperson"
    _description = "Receipt Salesperson"
    _rec_name = "name"

    name = fields.Char(
        string="Salesperson",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Portal User",
    )

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        required=True,
    )

    active = fields.Boolean(
        default=True,
    )