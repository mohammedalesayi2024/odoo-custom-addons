import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()

        for move in self:

            partner_lines = move.line_ids.filtered(
                lambda l: (
                    l.partner_id
                    and not l.reconciled
                    and (
                        (
                            l.account_id.account_type == "asset_receivable"
                            and l.credit > 0
                        )
                        or (
                            l.account_id.account_type == "liability_payable"
                            and l.debit > 0
                        )
                    )
                )
            )

            for payment_line in partner_lines:

                partner = payment_line.partner_id

                if not partner.auto_fifo_reconcile:
                    continue

                if payment_line.account_id.account_type == "asset_receivable":
                    account_type = "asset_receivable"
                    balance_operator = ">"
                    invoice_type = "out_invoice"

                elif payment_line.account_id.account_type == "liability_payable":
                    account_type = "liability_payable"
                    balance_operator = "<"
                    invoice_type = "in_invoice"

                else:
                    continue

                _logger.info(
                    "FIFO JOURNAL START | MOVE=%s | PARTNER=%s",
                    move.name,
                    partner.name,
                )

                method = partner.payment_allocation_method

                domain = [
                    ("partner_id", "=", partner.id),
                    ("account_id.account_type", "=", account_type),
                    ("parent_state", "=", "posted"),
                    ("reconciled", "=", False),
                ]

                if balance_operator == ">":
                    domain.append(("balance", ">", 0))
                else:
                    domain.append(("balance", "<", 0))

                if method == "date":

                    receivable_lines = self.env["account.move.line"].search(
                        domain,
                        order="date asc, id asc",
                    )

                else:

                    all_lines = self.env["account.move.line"].search(domain)

                    non_invoice_lines = all_lines.filtered(
                        lambda l: l.move_id.move_type != invoice_type
                    ).sorted(
                        key=lambda l: (
                            l.date or l.move_id.date,
                            l.id,
                        )
                    )

                    invoice_lines = all_lines.filtered(
                        lambda l: l.move_id.move_type == invoice_type
                    ).sorted(
                        key=lambda l: (
                            l.move_id.invoice_date_due
                            or l.move_id.invoice_date
                            or l.date,
                            l.id,
                        )
                    )

                    receivable_lines = non_invoice_lines + invoice_lines

                for line in receivable_lines:

                    if line.id == payment_line.id:
                        continue

                    try:
                        (payment_line + line).reconcile()

                    except Exception:
                        _logger.exception(
                            "FIFO JOURNAL RECONCILE ERROR"
                        )
                        raise

                    if payment_line.reconciled:
                        break

        return res