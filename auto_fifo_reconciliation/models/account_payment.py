from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()

        for payment in self:
            payment._auto_reconcile_oldest_invoices()

        return res

    def _auto_reconcile_oldest_invoices(self):
        self.ensure_one()

        # للعملاء فقط
        if self.partner_type != 'customer':
            return

        # سطر الذمم المدينة الخاص بالدفعة
        payment_line = self.move_id.line_ids.filtered(
            lambda l: (
                l.account_id.account_type == 'asset_receivable'
                and not l.reconciled
            )
        )

        if not payment_line:
            return

        payment_line = payment_line[0]

        # الفواتير المفتوحة مرتبة حسب تاريخ الاستحقاق
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ], order='invoice_date_due asc, id asc')

        for invoice in invoices:

            invoice_line = invoice.line_ids.filtered(
                lambda l: (
                    l.account_id.account_type == 'asset_receivable'
                    and not l.reconciled
                )
            )

            if not invoice_line:
                continue

            try:
                (payment_line + invoice_line[0]).reconcile()
            except Exception:
                continue

            # إذا انتهى مبلغ الدفعة نتوقف
            if payment_line.reconciled:
                break