from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    invoice_reference_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice Reference",
        compute="_compute_invoice_reference",
        store=True,
        readonly=True,
        index=True,
    )

    @api.depends("move_id")
    def _compute_invoice_reference(self):
        for line in self:
            _logger.warning("FIELDS: %s", list(line.move_id._fields.keys()))
            line.invoice_reference_id = False
