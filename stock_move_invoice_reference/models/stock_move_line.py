from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    invoice_reference_id = fields.Many2one(
        "account.move",
        string="Invoice Reference",
        compute="_compute_invoice_reference",
        store=True,
        readonly=True,
        index=True,
    )

    @api.depends("move_id.account_move_id")
    def _compute_invoice_reference(self):
        for line in self:
            line.invoice_reference_id = line.move_id.account_move_id
