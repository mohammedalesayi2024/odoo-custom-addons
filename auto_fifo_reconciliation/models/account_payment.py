import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        raise UserError("FIFO TEST")
        res = super().action_post()
        

        for payment in self:
            payment._auto_reconcile_oldest_invoices()

        return res

    def _auto_reconcile_oldest_invoices(self):
        self.ensure_one()

        _logger.info("=== AUTO FIFO START %s ===", self.name)

        if self.partner_type != 'customer':
            _logger.info("Not customer")
            return

        payment_line = self.move_id.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
            and not l.reconciled
        )

        _logger.info("Payment lines found: %s", len(payment_line))

        if not payment_line:
            return

        payment_line = payment_line[0]

        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ], order='invoice_date_due asc, id asc')

        _logger.info("Invoices found: %s", len(invoices))

        for invoice in invoices:

            _logger.info("Invoice: %s", invoice.name)

            invoice_line = invoice.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable'
                and not l.reconciled
            )

            if not invoice_line:
                continue

            try:
                _logger.info("Trying reconcile")
                (payment_line + invoice_line[0]).reconcile()
                _logger.info("Reconcile success")
            except Exception as e:
                _logger.exception("Reconcile error: %s", e)

            if payment_line.reconciled:
                break