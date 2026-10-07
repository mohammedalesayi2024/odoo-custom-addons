from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        readonly=False,
        copy=False,
        domain="[('salesperson_id', '=', salesperson_id), ('company_id', '=', company_id), ('state', '!=', 'finished')]",
    )

    @api.onchange("salesperson_id")
    def _onchange_salesperson_id_multi(self):
        for payment in self:
            payment.receipt_book_id = False
            if payment.salesperson_id:
                payment.receipt_book_id = payment.env["receipt.book"].search([
                    ("salesperson_id", "=", payment.salesperson_id.id),
                    ("company_id", "=", payment.company_id.id),
                    ("state", "!=", "finished"),
                ], order="id desc", limit=1)

    def _get_receipt_book(self):
        self.ensure_one()
        if self.receipt_book_id:
            book = self.receipt_book_id
            if (
                book.salesperson_id == self.salesperson_id
                and book.company_id == self.company_id
                and book.state != "finished"
            ):
                return book
        return super()._get_receipt_book()
