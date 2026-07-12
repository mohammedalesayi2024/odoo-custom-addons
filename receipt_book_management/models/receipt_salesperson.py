from odoo import fields, models


class ReceiptSalesperson(models.Model):
    _name = "receipt.salesperson"
    _description = "Receipt Salesperson"
    _rec_name = "name"
    _order = "name"
    _sql_constraints = [
    (
        "unique_portal_user",
        "unique(user_id)",
        "This Portal User is already assigned to another salesperson.",
    ),
]
    name = fields.Char(
        string="Salesperson",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Portal User",
        required=True,
        domain=[("share", "=", True)],
    )

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        required=True,
    )

    active = fields.Boolean(
        default=True,
    )