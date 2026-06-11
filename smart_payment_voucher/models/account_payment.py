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
        
    @api.depends("amount", "currency_id")
    def _compute_amount_in_words(self):
        for rec in self:

         lang = rec.env.context.get("lang", "en_US")

         if lang.startswith("ar"):
            amount_text = num2words(rec.amount, lang="ar")

            if rec.currency_id.name == "SAR":
                currency_name = "ريال سعودي"
            elif rec.currency_id.name == "USD":
                currency_name = "دولار أمريكي"
            elif rec.currency_id.name == "EUR":
                currency_name = "يورو"
            else:
                currency_name = rec.currency_id.name

            rec.amount_in_words = (
                f"{amount_text} {currency_name} فقط لا غير"
            )

        else:
            amount_text = num2words(rec.amount, lang="en")

            if rec.currency_id.name == "SAR":
                currency_name = "Saudi Riyals"
            elif rec.currency_id.name == "USD":
                currency_name = "US Dollars"
            elif rec.currency_id.name == "EUR":
                currency_name = "Euros"
            else:
                currency_name = rec.currency_id.name

            rec.amount_in_words = (
                f"{amount_text} {currency_name} Only"
            )