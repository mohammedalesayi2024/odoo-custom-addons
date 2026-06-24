from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    auto_fifo_reconcile = fields.Boolean(
        string="Auto FIFO Reconciliation",
        default=False,
        help="Automatically reconcile payments with oldest open items."
    )

    payment_allocation_method = fields.Selection(
        [
            ("date", "By Transaction Date"),
            ("due_date", "By Due Date"),
        ],
        string="Payment Allocation Method",
        default="date",
        help="Choose how automatic reconciliation prioritizes open items."
    )