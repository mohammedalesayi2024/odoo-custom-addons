# models/partner.py

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    auto_fifo_reconcile = fields.Boolean(
        string="Auto FIFO Reconciliation",
        default=False,
        help="Automatically reconcile payments with oldest open items."
    )