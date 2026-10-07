from odoo import fields, models
from odoo.exceptions import ValidationError


class ReceiptDelayedWizard(models.TransientModel):
    _name = "receipt.delayed.wizard"
    _description = "Receipt Delayed Wizard"

    payment_id = fields.Many2one(
        "account.payment",
        required=True,
        ondelete="cascade",
    )

    delayed_exception_id = fields.Many2one(
        "receipt.exception",
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()

        exception = self.delayed_exception_id

        if not exception:
            raise ValidationError("Delayed receipt was not found.")

        exception.write(
            {
                "resolved": True,
                "resolved_by": self.env.user.id,
                "resolved_date": fields.Datetime.now(),
            }
        )
        self.payment_id.with_context(skip_receipt_exception_check=True).action_post()
        return {
            "type": "ir.actions.act_window_close",
        }
