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

            # -------------------------
            # Sales
            # -------------------------
            sale_line = line.move_id.sale_line_id
            if sale_line:
                invoice_line = sale_line.invoice_lines.filtered(
                    lambda l: l.move_id.state == "posted"
                    and l.move_id.move_type == "out_invoice"
                )[:1]

                if invoice_line:
                    line.invoice_reference_id = invoice_line.move_id
                    continue

            # -------------------------
            # Purchase
            # -------------------------
            purchase_line = line.move_id.purchase_line_id
            if purchase_line:
                invoice_line = purchase_line.invoice_lines.filtered(
                    lambda l: l.move_id.state == "posted"
                    and l.move_id.move_type == "in_invoice"
                )[:1]

                if invoice_line:
                    line.invoice_reference_id = invoice_line.move_id
