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

            lang = rec.env.user.lang or "en_US"

            whole_part = int(rec.amount)
            fraction_part = round((rec.amount - whole_part) * 100)

            if lang.startswith("ar"):

                amount_text = num2words(whole_part, lang="ar")
                fraction_text = num2words(fraction_part, lang="ar")

                if rec.currency_id.name == "SAR":

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text} ريال سعودي "
                            f"و {fraction_text} هللة فقط لا غير"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text} ريال سعودي فقط لا غير"
                        )

                elif rec.currency_id.name == "USD":

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text} دولار أمريكي "
                            f"و {fraction_text} سنت فقط لا غير"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text} دولار أمريكي فقط لا غير"
                        )

                elif rec.currency_id.name == "EUR":

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text} يورو "
                            f"و {fraction_text} سنت فقط لا غير"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text} يورو فقط لا غير"
                        )

                else:

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text} {rec.currency_id.name} "
                            f"و {fraction_text} فقط لا غير"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text} {rec.currency_id.name} فقط لا غير"
                        )

            else:

                amount_text = num2words(whole_part, lang="en")
                fraction_text = num2words(fraction_part, lang="en")

                if rec.currency_id.name == "SAR":

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text.title()} Riyals Saudi "
                            f"and {fraction_text.title()} Halalas Only"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text.title()} Riyals Saudi Only"
                        )

                elif rec.currency_id.name == "USD":

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text.title()} US Dollars "
                            f"and {fraction_text.title()} Cents Only"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text.title()} US Dollars Only"
                        )

                elif rec.currency_id.name == "EUR":

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text.title()} Euros "
                            f"and {fraction_text.title()} Cents Only"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text.title()} Euros Only"
                        )

                else:

                    if fraction_part:
                        rec.amount_in_words = (
                            f"{amount_text.title()} {rec.currency_id.name} "
                            f"and {fraction_text.title()} Only"
                        )
                    else:
                        rec.amount_in_words = (
                            f"{amount_text.title()} {rec.currency_id.name} Only"
                        )