from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        domain=[("share", "=", True)],
        help="Select the salesperson who owns the receipt book.",
    )

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        readonly=True,
        copy=False,
    )

    receipt_number = fields.Integer(
        string="Receipt Number",
        copy=False,
    )

    @api.onchange("salesperson_id")
    def _onchange_salesperson_id(self):
        self.receipt_book_id = False

        if not self.salesperson_id:
            return

        self.receipt_book_id = self._get_receipt_book()

    def _check_delayed_receipt(self, book):
        self.ensure_one()

        if not book:
            return False

        return self.env["receipt.exception"].search(
            [
                ("receipt_book_id", "=", book.id),
                ("receipt_number", "=", self.receipt_number),
                ("reason", "=", "delayed"),
                ("resolved", "=", False),
            ],
            limit=1,
        )

    def _get_receipt_book(self):
        self.ensure_one()

        if not self.salesperson_id:
            return False

        return self.env["receipt.book"].search(
            [
                ("salesperson_id", "=", self.salesperson_id.id),
                ("company_id", "=", self.company_id.id),
            ],
            order="id desc",
            limit=1,
        )

    def write(self, vals):
        protected_fields = {
            "salesperson_id",
            "receipt_book_id",
            "receipt_number",
        }

        if protected_fields.intersection(vals):
            for payment in self:
                if payment.state == "posted":
                    raise ValidationError(
                        _(
                            "You cannot modify the Salesperson or Receipt information on a posted payment. Reset the payment to Draft first."
                        )
                    )

        return super().write(vals)

    def action_post(self):

        for payment in self:

            # Customer Receipts Only
            if payment.payment_type != "inbound":
                continue

            if payment.partner_type != "customer":
                continue

            # No Salesperson -> Normal Odoo Posting
            if not payment.salesperson_id:
                continue

            book = payment._get_receipt_book()

            if not book:
                raise ValidationError(
                    _("The selected salesperson has no Receipt Book.")
                )

            if book.next_number > book.to_number:
                raise ValidationError(
                    _("The selected Receipt Book has no remaining receipt numbers.")
                )
            is_reposting = (
                payment.receipt_book_id
                and payment.receipt_book_id == book
                and payment.receipt_number
            )
            # Auto assign next receipt number
            if not payment.receipt_number:
                payment.receipt_number = book.next_number

            if (
                not is_reposting
                and not self.env.context.get("skip_receipt_exception_check")
                and payment.receipt_number < book.next_number
            ):

                delayed_exception = self.env["receipt.exception"].search(
                    [
                        ("receipt_book_id", "=", book.id),
                        ("receipt_number", "=", payment.receipt_number),
                        ("reason", "=", "delayed"),
                        ("resolved", "=", False),
                    ],
                    limit=1,
                )

                if not delayed_exception:
                    raise ValidationError(
                        _(
                            "Receipt Number cannot be less than the next expected receipt number."
                        )
                    )

            if payment.receipt_number > book.to_number:
                raise ValidationError(
                    _("Receipt Number exceeds the Receipt Book range.")
                )

            existing_payment = self.search(
                [
                    ("id", "!=", payment.id),
                    ("receipt_book_id", "=", book.id),
                    ("receipt_number", "=", payment.receipt_number),
                    ("state", "=", "posted"),
                ],
                limit=1,
            )

            if existing_payment:
                raise ValidationError(
                    _("Receipt Number already exists in this Receipt Book.")
                )

            delayed_exception = payment._check_delayed_receipt(book)

            if delayed_exception:

                wizard = self.env["receipt.delayed.wizard"].create(
                    {
                        "payment_id": payment.id,
                        "delayed_exception_id": delayed_exception.id,
                    }
                )

                return {
                    "type": "ir.actions.act_window",
                    "name": _("Delayed Receipt"),
                    "res_model": "receipt.delayed.wizard",
                    "view_mode": "form",
                    "res_id": wizard.id,
                    "target": "new",
                }

            # Skipped receipt numbers
            if not self.env.context.get("skip_receipt_exception_check"):

                skipped_numbers = list(range(book.next_number, payment.receipt_number))

                if skipped_numbers:

                    wizard = self.env["receipt.exception.wizard"].create(
                        {
                            "payment_id": payment.id,
                            "receipt_book_id": book.id,
                        }
                    )

                    for number in skipped_numbers:
                        self.env["receipt.exception.wizard.line"].create(
                            {
                                "wizard_id": wizard.id,
                                "receipt_number": number,
                            }
                        )

                    return {
                        "type": "ir.actions.act_window",
                        "name": _("Skipped Receipt Numbers"),
                        "res_model": "receipt.exception.wizard",
                        "view_mode": "form",
                        "res_id": wizard.id,
                        "target": "new",
                    }

            payment.receipt_book_id = book

            result = super().action_post()
            if (
                not self.env.context.get("skip_receipt_exception_check")
                and payment.receipt_number >= book.next_number
            ):
                book.write(
                    {
                        "next_number": payment.receipt_number + 1,
                    }
                )

            return result

        return super().action_post()
