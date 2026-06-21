from odoo import models
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()

        for payment in self:
            _logger.info("AUTO RECONCILE START %s", payment.name)
            payment._auto_reconcile_oldest_invoices()

        return res

    def _auto_reconcile_oldest_invoices(self):
        self.ensure_one()

        _logger.info("Partner: %s", self.partner_id.name)
        _logger.info("Move: %s", self.move_id.name)

        for line in self.move_id.line_ids:
            _logger.info(
                "Account=%s Type=%s Debit=%s Credit=%s",
                line.account_id.code,
                line.account_id.account_type,
                line.debit,
                line.credit,
            )