from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    invoice_reference_id = fields.Many2one(
        "account.move",
        string="Invoice Reference",
        compute="_compute_invoice_reference",
        readonly=True,
        store=False,
    )

    @api.depends("move_id.sale_line_id", "move_id.purchase_line_id")
    def _compute_invoice_reference(self):
        for line in self:
            line.invoice_reference_id = False

            # Customer Invoice / Credit Note
            if line.move_id.sale_line_id:
                order = line.move_id.sale_line_id.order_id
                invoice = order.invoice_ids.filtered(
                    lambda m: m.state == "posted"
                    and m.move_type in ("out_invoice", "out_refund")
                )[:1]

                if invoice:
                    line.invoice_reference_id = invoice
                continue

            # Vendor Bill / Vendor Credit Note
            if line.move_id.purchase_line_id:
                order = line.move_id.purchase_line_id.order_id
                invoice = order.invoice_ids.filtered(
                    lambda m: m.state == "posted"
                    and m.move_type in ("in_invoice", "in_refund")
                )[:1]

                if invoice:
                    line.invoice_reference_id = invoice
