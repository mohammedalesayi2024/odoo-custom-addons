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
        domain='[("salesperson_id", "=", salesperson_multi_id), ("company_id", "=", company_id), ("state", "!=", "finished")]',
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
                ("receipt_book_id", "=", book.id),
                ("receipt_number", "=", self.receipt_number_multi),
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
            order="id asc",
            limit=1,
        )

    @api.onchange("partner_id")
    def _onchange_partner_id_salesperson(self):
        for payment in self:
            if payment.partner_id:
                payment.salesperson_multi_id = payment.partner_id.user_id
            else:
                payment.salesperson_multi_id = False
    
    @api.onchange("receipt_number_multi", "receipt_book_multi_id")
    def _onchange_receipt_number_multi_warning(self):
        for payment in self:
            if not payment.receipt_book_multi_id or not payment.receipt_number_multi:
                continue

            existing_payment = self.search(
                [
                    ("id", "!=", payment._origin.id or 0),
                    ("receipt_book_multi_id", "=", payment.receipt_book_multi_id.id),
                    ("receipt_number_multi", "=", payment.receipt_number_multi),
                ],
                limit=1,
            )
            if existing_payment:
                return {
                    "warning": {
                        "title": _("Duplicate Receipt Number"),
                        "message": _(
                            "Receipt number %(number)s is already assigned to payment %(payment)s in this receipt book. "
                            "Please enter a different receipt number."
                        ) % {
                            "number": payment.receipt_number_multi,
                            "payment": existing_payment.display_name,
                        },
                    }
                }

            old_number = payment._origin.receipt_number_multi
            if (
                payment.state == "draft"
                and old_number
                and payment.receipt_number_multi
                and old_number != payment.receipt_number_multi
            ):
                return {
                    "warning": {
                        "title": _("Receipt Number Changed"),
                        "message": _(
                            "This receipt already has number %(old)s. "
                            "You are changing it to %(new)s. "
                            "Please make sure this change is intentional. "
                            "The receipt book sequence will follow the existing logic."
                        ) % {
                            "old": old_number,
                            "new": payment.receipt_number_multi,
                        },
                    }
                }

    @api.constrains("receipt_book_multi_id", "receipt_number_multi", "payment_type", "partner_type")
    def _check_unique_receipt_number_multi(self):
        for payment in self:
            if (
                payment.payment_type != "inbound"
                or payment.partner_type != "customer"
                or not payment.receipt_book_multi_id
                or not payment.receipt_number_multi
            ):
                continue

            duplicate = self.search(
                [
                    ("id", "!=", payment.id),
                    ("receipt_book_multi_id", "=", payment.receipt_book_multi_id.id),
                    ("receipt_number_multi", "=", payment.receipt_number_multi),
                ],
                limit=1,
            )
            # Validate that the receipt number belongs to the selected receipt book.
            # This runs when saving a Draft payment as well as during later updates.
            book = payment.receipt_book_multi_id
            number = payment.receipt_number_multi
            if number < book.from_number or number > book.to_number:
                raise ValidationError(
                    _(
                        "Receipt number %(number)s is outside the range for receipt book "
                        "%(book)s. Allowed range: %(start)s to %(end)s."
                    ) % {
                        "number": number,
                        "book": book.display_name,
                        "start": book.from_number,
                        "end": book.to_number,
                    }
                )

            if duplicate:
                raise ValidationError(
                    _(
                        "Receipt number %(number)s is already assigned to payment %(payment)s "
                        "in receipt book %(book)s. Each receipt number can be used only once."
                    ) % {
                        "number": payment.receipt_number_multi,
                        "payment": duplicate.display_name,
                        "book": payment.receipt_book_multi_id.display_name,
                    }
                )

    def write(self, vals):
        protected_fields = {
            "salesperson_multi_id",
            "receipt_book_multi_id",
            "receipt_number_multi",
        }

        if "receipt_number_multi" in vals:
            new_number = vals.get("receipt_number_multi") or 0
            for payment in self:
                if (
                    payment.state == "draft"
                    and payment.receipt_number_multi
                    and new_number
                    and new_number < payment.receipt_number_multi
                ):
                    raise ValidationError(
                        _(
                            "The receipt number cannot be reduced from %(old)s to %(new)s. "
                            "Please keep the current receipt number or use a higher number."
                        ) % {
                            "old": payment.receipt_number_multi,
                            "new": new_number,
                        }
                    )

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
                        ("receipt_book_id", "=", book.id),
                        ("receipt_number", "=", payment.receipt_number_multi),
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

                skipped_numbers = list(
                    range(book.next_number, payment.receipt_number_multi)
                )

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
