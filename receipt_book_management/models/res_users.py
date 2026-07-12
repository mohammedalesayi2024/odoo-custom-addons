from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book"
    )