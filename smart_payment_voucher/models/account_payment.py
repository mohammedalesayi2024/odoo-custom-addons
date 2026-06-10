from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_print_receipt_voucher(self):
        self.ensure_one()

        return self.env.ref(
            "smart_payment_voucher.action_receipt_voucher"
        ).report_action(self)

    def action_print_payment_voucher(self):
        self.ensure_one()

        return self.env.ref(
            "smart_payment_voucher.action_payment_voucher"
        ).report_action(self)