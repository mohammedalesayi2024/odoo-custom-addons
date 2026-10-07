from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ReceiptExceptionWizard(models.TransientModel):
    _name = "receipt.exception.wizard.multi"
    _description = "Receipt Exception Wizard"

    payment_id = fields.Many2one(
        "account.payment",
        required=True,
        ondelete="cascade",
    )

    receipt_book_id = fields.Many2one(
        "receipt.book.multi",
        string="Receipt Book",
        required=True,
    )

    line_ids = fields.One2many(
        "receipt.exception.wizard.line.multi",
        "wizard_id",
        string="Skipped Receipts",
    )

    def action_confirm(self):
        self.ensure_one()

        payment = self.payment_id
        book = self.receipt_book_id

        if not book:
            raise ValidationError("Receipt Book not found.")
        for line in self.line_ids:
            if not line.reason:
                raise ValidationError(
                    _(
                        "Please select a reason for every skipped receipt before confirming."
                    )
                )
        for line in self.line_ids:
            self.env["receipt.exception.multi"].create(
                {
                    "receipt_book_id": book.id,
                    "receipt_number": line.receipt_number,
                    "reason": line.reason,
                    "description": line.notes or "",
                }
            )
            # Move Next Number after the posted receipt
        if book.next_number <= payment.receipt_number_multi:
            book.write(
                {
                    "next_number": payment.receipt_number_multi + 1,
                }
            )
        payment.with_context(skip_receipt_exception_check=True).action_post()
        return {
            "type": "ir.actions.act_window_close",
        }


class ReceiptExceptionWizardLine(models.TransientModel):
    _name = "receipt.exception.wizard.line.multi"
    _description = "Receipt Exception Wizard Line"

    wizard_id = fields.Many2one(
        "receipt.exception.wizard.multi",
        required=True,
        ondelete="cascade",
    )

    receipt_number = fields.Integer(
        string="Receipt Number",
        readonly=True,
    )

    reason = fields.Selection(
        [
            ("lost", "Lost"),
            ("damaged", "Damaged"),
            ("cancelled", "Cancelled"),
            ("delayed", "Delayed"),
        ],
        string="Reason",
    )

    notes = fields.Text(
        string="Notes",
    )
