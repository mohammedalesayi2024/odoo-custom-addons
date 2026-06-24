import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()

        for move in self:

            _logger.info("===== MOVE %s =====", move.name)

            for line in move.line_ids:

                _logger.info(
                    "ACCOUNT=%s | TYPE=%s | PARTNER=%s | DEBIT=%s | CREDIT=%s",
                    line.account_id.code,
                    line.account_id.account_type,
                    line.partner_id.name if line.partner_id else "NONE",
                    line.debit,
                    line.credit,
                )

        return res