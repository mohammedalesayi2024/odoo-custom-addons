from odoo import api, models, _
from odoo.exceptions import ValidationError


class ReceiptBook(models.Model):
    _inherit = "receipt.book"

    @api.constrains("salesperson_id", "state", "from_number", "to_number", "company_id")
    def _check_active_book(self):
        """
        Replace the original one-active-book rule.

        Multiple receipt books are allowed for the same salesperson.
        Active/non-finished books for the same salesperson/company must not
        have overlapping number ranges.
        """
        for rec in self:
            if rec.state == "finished":
                continue

            overlapping_books = self.search([
                ("id", "!=", rec.id),
                ("salesperson_id", "=", rec.salesperson_id.id),
                ("company_id", "=", rec.company_id.id),
                ("state", "!=", "finished"),
                ("from_number", "<=", rec.to_number),
                ("to_number", ">=", rec.from_number),
            ], limit=1)

            if overlapping_books:
                raise ValidationError(_(
                    "The receipt number range overlaps with another Receipt Book "
                    "for this salesperson. Please use a different number range."
                ))
