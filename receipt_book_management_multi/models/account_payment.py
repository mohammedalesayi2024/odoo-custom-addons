from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    salesperson_multi_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        domain=[("share", "=", True)],
        help="Select the salesperson who owns the receipt book.",
    )

    receipt_book_multi_id = fields.Many2one(
        "receipt.book.multi",
        string="Receipt Book",
        readonly=False,
        copy=False,
        domain="[(\"salesperson_id\", \"=\", salesperson_multi_id), (\"company_id\", \"=\", company_id), (\"state\", \"!=\", \"finished\")]",
    )

    receipt_number_multi = fields.Integer(
        string="Receipt Number",
        copy=False,
    )

    @api.onchange("salesperson_multi_id")
    def _onchange_salesperson_id(self):
        self.receipt_book_multi_id = False

        if not self.salesperson_multi_id:
            return

        self.receipt_book_multi_id = self._get_receipt_book()

    def _check_delayed_receipt(self, book):
        self.ensure_one()

        if not book:
            return False

        return self.env["receipt.exception.multi"].search(
            [
                ("receipt_book_multi_id", "=", book.id),
                ("receipt_number_multi", "=", self.receipt_number_multi),
                ("reason", "=", "delayed"),
                ("resolved", "=", False),
            ],
            limit=1,
        )

    def _get_receipt_book(self):
        self.ensure_one()

        if not self.salesperson_multi_id:
            return False

        if (
            self.receipt_book_multi_id
            and self.receipt_book_multi_id.salesperson_id == self.salesperson_multi_id
            and self.receipt_book_multi_id.company_id == self.company_id
            and self.receipt_book_multi_id.state != "finished"
        ):
            return self.receipt_book_multi_id

        return self.env["receipt.book.multi"].search(
            [
                ("salesperson_id", "=", self.salesperson_multi_id.id),
                ("company_id", "=", self.company_id.id),
                ("state", "!=", "finished"),
            ],
            order="id desc",
            limit=1,
        )

    def write(self, vals):
        protected_fields = {
            "salesperson_multi_id",
            "receipt_book_multi_id",
            "receipt_number_multi",
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
            if not payment.salesperson_multi_id:
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
                payment.receipt_book_multi_id
                and payment.receipt_book_multi_id == book
                and payment.receipt_number_multi
            )
            # Auto assign next receipt number
            if not payment.receipt_number_multi:
                payment.receipt_number_multi = book.next_number

            if (
                not is_reposting
                and not self.env.context.get("skip_receipt_exception_check")
                and payment.receipt_number_multi < book.next_number
            ):

                delayed_exception = self.env["receipt.exception.multi"].search(
                    [
                        ("receipt_book_multi_id", "=", book.id),
                        ("receipt_number_multi", "=", payment.receipt_number_multi),
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

            if payment.receipt_number_multi > book.to_number:
                raise ValidationError(
                    _("Receipt Number exceeds the Receipt Book range.")
                )

            existing_payment = self.search(
                [
                    ("id", "!=", payment.id),
                    ("receipt_book_multi_id", "=", book.id),
                    ("receipt_number_multi", "=", payment.receipt_number_multi),
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

                wizard = self.env["receipt.delayed.wizard.multi"].create(
                    {
                        "payment_id": payment.id,
                        "delayed_exception_id": delayed_exception.id,
                    }
                )

                return {
                    "type": "ir.actions.act_window",
                    "name": _("Delayed Receipt"),
                    "res_model": "receipt.delayed.wizard.multi",
                    "view_mode": "form",
                    "res_id": wizard.id,
                    "target": "new",
                }

            # Skipped receipt numbers
            if not self.env.context.get("skip_receipt_exception_check"):

                skipped_numbers = list(range(book.next_number, payment.receipt_number_multi))

                if skipped_numbers:

                    wizard = self.env["receipt.exception.wizard.multi"].create(
                        {
                            "payment_id": payment.id,
                            "receipt_book_id": book.id,
                        }
                    )

                    for number in skipped_numbers:
                        self.env["receipt.exception.wizard.line.multi"].create(
                            {
                                "wizard_id": wizard.id,
                                "receipt_number": number,
                            }
                        )

                    return {
                        "type": "ir.actions.act_window",
                        "name": _("Skipped Receipt Numbers"),
                        "res_model": "receipt.exception.wizard.multi",
                        "view_mode": "form",
                        "res_id": wizard.id,
                        "target": "new",
                    }

            payment.receipt_book_multi_id = book

            result = super().action_post()
            if (
                not self.env.context.get("skip_receipt_exception_check")
                and payment.receipt_number_multi >= book.next_number
            ):
                book.write(
                    {
                        "next_number": payment.receipt_number_multi + 1,
                    }
                )

            return result

        return super().action_post()
