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
    )

    @api.depends("move_id.sale_line_id")
    def _compute_invoice_reference(self):
        for line in self:
            line.invoice_reference_id = False

            sale_line = line.move_id.sale_line_id
            if not sale_line:
                _logger.warning("NO SALE LINE")
                continue

            order = sale_line.order_id
            _logger.warning("ORDER: %s", order.name)

            _logger.warning("INVOICE IDS: %s", order.invoice_ids.ids)

            for inv in order.invoice_ids:
                _logger.warning(
                    "Invoice: %s  state=%s  type=%s",
                    inv.name,
                    inv.state,
                    inv.move_type,
                )

            invoices = order.invoice_ids.filtered(
                lambda m: m.state == "posted"
                and m.move_type in ("out_invoice", "out_refund")
            )

            if invoices:
                line.invoice_reference_id = invoices[0]
