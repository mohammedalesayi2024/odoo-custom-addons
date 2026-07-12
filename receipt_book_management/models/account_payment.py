from odoo import fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        readonly=True,
        copy=False,
    )

    receipt_number = fields.Integer(
        string="Receipt Number",
        readonly=True,
        copy=False,
    )

    def action_post(self):
        res = super().action_post()

        for payment in self:

            # فقط سندات القبض من العملاء
            if payment.payment_type != "inbound":
                continue

            if payment.partner_type != "customer":
                continue

            book = payment.env.user.receipt_book_id

            if not book:
                raise ValidationError("Please assign a Receipt Book to your user.")

            if book.next_number > book.to_number:
                raise ValidationError("Receipt Book has no remaining numbers.")

            payment.receipt_book_id = book
            payment.receipt_number = book.next_number

            book.next_number += 1

        return res