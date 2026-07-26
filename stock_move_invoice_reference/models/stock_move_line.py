from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    invoice_reference_id = fields.Many2one(
        "account.move",
        string="Invoice Reference",
        compute="_compute_invoice_reference",
        store=False,
        readonly=True,
    )

    @api.depends("move_id.sale_line_id", "move_id.purchase_line_id")
    def _compute_invoice_reference(self):
        for line in self:
            line.invoice_reference_id = False

            # Sales
            if line.move_id.sale_line_id:
                order = line.move_id.sale_line_id.order_id
                invoices = order.invoice_ids.filtered(
                    lambda m: m.state == "posted"
                    and m.move_type in ("out_invoice", "out_refund")
                )
                if invoices:
                    line.invoice_reference_id = invoices[0]
                continue

            # Purchase
            purchase_line = line.move_id.purchase_line_id
            if not purchase_line:
                _logger.warning("NO PURCHASE LINE")
                continue

            purchase = purchase_line.order_id

            _logger.warning("PURCHASE: %s", purchase.name)
            _logger.warning("INVOICE IDS: %s", purchase.invoice_ids.ids)

            for inv in purchase.invoice_ids:
                _logger.warning(
                    "Vendor Bill: %s state=%s type=%s",
                    inv.name,
                    inv.state,
                    inv.move_type,
                )
