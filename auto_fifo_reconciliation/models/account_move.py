import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()

        for move in self:

            receivable_credit_lines = move.line_ids.filtered(
                lambda l: (
                    l.account_id.account_type == "asset_receivable"
                    and l.partner_id
                    and l.credit > 0
                )
            )

            for line in receivable_credit_lines:

                partner = line.partner_id

                _logger.info(
                    "FIFO JOURNAL | MOVE=%s | PARTNER=%s | CREDIT=%s",
                    move.name,
                    partner.name,
                    line.credit,
                )

        return res