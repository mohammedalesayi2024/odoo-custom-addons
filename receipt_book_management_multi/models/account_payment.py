from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        readonly=False,
        copy=False,
    )

    def _get_receipt_book(self):
        """
        Use the receipt book explicitly selected on the payment.
        If none is selected, preserve the original behavior and use the
        latest available receipt book.
        """
        self.ensure_one()

        if not self.salesperson_id:
            return False

        if (
            self.receipt_book_id
            and self.receipt_book_id.salesperson_id == self.salesperson_id
            and self.receipt_book_id.company_id == self.company_id
            and self.receipt_book_id.state != "finished"
        ):
            return self.receipt_book_id

        return self.env["receipt.book"].search(
            [
                ("salesperson_id", "=", self.salesperson_id.id),
                ("company_id", "=", self.company_id.id),
                ("state", "!=", "finished"),
            ],
            order="id desc",
            limit=1,
        )
