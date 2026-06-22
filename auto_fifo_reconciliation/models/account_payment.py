import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()

        for payment in self:
            partner = payment.partner_id

            if partner.auto_fifo_reconcile:
                payment._auto_reconcile_oldest_invoices()

        return res

    def _auto_reconcile_oldest_invoices(self):
        self.ensure_one()

        if not self.partner_id:
            return

        _logger.info("=== AUTO FIFO START %s ===", self.name)

        if self.payment_type != "inbound" or self.partner_type != "customer":
            _logger.info("Not inbound customer payment")
            return

        payment_line = self.move_id.line_ids.filtered(
            lambda l: (
                l.account_id.account_type == "asset_receivable"
                and not l.reconciled
            )
        )

        _logger.info("Payment lines found: %s", len(payment_line))

        if not payment_line:
            return

        if len(payment_line) != 1:
            _logger.warning(
                "Expected 1 receivable payment line, found %s",
                len(payment_line),
            )

        payment_line = payment_line[0]

        receivable_lines = self.env["account.move.line"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("account_id.account_type", "=", "asset_receivable"),
                ("parent_state", "=", "posted"),
                ("reconciled", "=", False),
                ("balance", ">", 0),
            ],
            order="date asc, id asc",
        )

        _logger.info("=== RECEIVABLE LINES ===")

        for line in receivable_lines:
            _logger.info(
                "MOVE=%s | PARTNER=%s | BALANCE=%s | RESIDUAL=%s | ID=%s",
                line.move_id.name,
                line.partner_id.name,
                line.balance,
                line.amount_residual,
                line.id,
            )

        _logger.info("Receivable lines found: %s", len(receivable_lines))

        for line in receivable_lines:

            if line.id == payment_line.id:
                continue

            _logger.info(
                "Processing line %s | Move=%s | Residual=%s",
                line.id,
                line.move_id.name,
                line.amount_residual,
            )

            try:
                _logger.info("Trying reconcile")
                (payment_line + line).reconcile()
                _logger.info("Reconcile success")

            except Exception:
                _logger.exception("Reconcile error")
                raise

            if payment_line.reconciled:
                _logger.info("Payment fully reconciled")
                break

        _logger.info("=== AUTO FIFO END %s ===", self.name)