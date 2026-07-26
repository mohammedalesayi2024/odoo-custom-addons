from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    invoice_reference_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice Reference",
        compute="_compute_invoice_reference",
        readonly=True,
        store=False,
    )

    @api.depends("move_id.sale_line_id")
    def _compute_invoice_reference(self):
        for line in self:
            line.invoice_reference_id = False

            sale_line = line.move_id.sale_line_id
            if not sale_line:
                continue

            order = sale_line.order_id
            if not order:
                continue

            invoices = order.invoice_ids.filtered(
                lambda m: m.state == "posted"
                and m.move_type in ("out_invoice", "out_refund")
            )

            if invoices:
                line.invoice_reference_id = invoices[0]
