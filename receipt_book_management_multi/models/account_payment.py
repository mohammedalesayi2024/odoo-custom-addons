from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # The original module makes this field readonly.  This extension allows
    # choosing one of the salesperson's active receipt books before posting.
    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        readonly=False,
        copy=False,
        domain="[('salesperson_id', '=', salesperson_id), ('company_id', '=', company_id), ('state', '!=', 'finished')]",
    )

    def _get_receipt_book(self):
        """Use the manually selected book; otherwise keep original behavior."""
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
