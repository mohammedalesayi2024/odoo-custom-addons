from odoo import api, models, _
from odoo.exceptions import ValidationError


class ReceiptBook(models.Model):
    _inherit = "receipt.book"

    @api.constrains("salesperson_id", "state")
    def _check_active_book(self):
        """Disable the original one-active-book restriction.

        The original module uses this constraint to prevent a salesperson
        from having more than one unfinished receipt book.  This extension
        intentionally replaces that behavior because a salesperson may now
        own multiple books simultaneously.
        """
        return True

    @api.constrains("salesperson_id", "company_id", "from_number", "to_number")
    def _check_receipt_book_range_overlap(self):
        """Prevent overlapping receipt-number ranges for the same owner."""
        for book in self:
            if not book.salesperson_id or not book.from_number or not book.to_number:
                continue

            overlapping = self.search(
                [
                    ("id", "!=", book.id),
                    ("salesperson_id", "=", book.salesperson_id.id),
                    ("company_id", "=", book.company_id.id),
                    ("from_number", "<=", book.to_number),
                    ("to_number", ">=", book.from_number),
                ],
                limit=1,
            )

            if overlapping:
                raise ValidationError(
                    _(
                        "The receipt number range %(new_from)s-%(new_to)s overlaps "
                        "with Receipt Book '%(book)s' (%(old_from)s-%(old_to)s) "
                        "for this salesperson."
                    )
                    % {
                        "new_from": book.from_number,
                        "new_to": book.to_number,
                        "book": overlapping.name,
                        "old_from": overlapping.from_number,
                        "old_to": overlapping.to_number,
                    }
                )
