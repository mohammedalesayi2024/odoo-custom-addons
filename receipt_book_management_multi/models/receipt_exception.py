from odoo import fields, models, _


class ReceiptException(models.Model):
    _name = "receipt.exception.multi"
    _description = "Receipt Exception"
    _order = "receipt_number desc"

    receipt_book_id = fields.Many2one(
        "receipt.book.multi",
        string="Receipt Book",
        required=True,
        ondelete="cascade",
    )

    receipt_number = fields.Integer(
        string="Receipt Number",
        required=True,
    )

    reason = fields.Selection(
        [
            ("lost", "Lost"),
            ("damaged", "Damaged"),
            ("cancelled", "Cancelled"),
            ("delayed", "Delayed"),
        ],
        string="Reason",
        required=True,
        
    )
    
    description = fields.Text(
        string="Description",
    )
    resolved = fields.Boolean(
       string="Resolved",
       default=False,
       readonly=True,
    )
    resolved_by = fields.Many2one(
       "res.users",
       string="Resolved By",
       readonly=True,
   )
    resolved_date = fields.Datetime(
       string="Resolved Date",
       readonly=True,
  )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="receipt_book_id.company_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "receipt_exception_multi_unique",
            "unique(receipt_book_id, receipt_number)",
            "This receipt number has already been registered as an exception.",
        ),
    ]