from odoo import models
from odoo import models, fields, api
from num2words import num2words

class AccountPayment(models.Model):
    _inherit = "account.payment"
    amount_in_words = fields.Char(
        string="Amount In Words",
        compute="_compute_amount_in_words"
    )

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
        

    @api.depends("amount")
    def _compute_amount_in_words(self):
        for rec in self:
            rec.amount_in_words = num2words(rec.amount, lang='ar')