from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    salesperson_id = fields.Many2one(
        "receipt.salesperson",
        string="Salesperson",
    )

    receipt_book_id = fields.Many2one(
        "receipt.book",
        string="Receipt Book",
        readonly=True,
        copy=False,
    )

    receipt_number = fields.Integer(
        string="Receipt Number",
        readonly=True,
        copy=False,
    )

    @api.onchange("salesperson_id")
    def _onchange_salesperson_id(self):
        for rec in self:
            if rec.salesperson_id:
                rec.receipt_book_id = rec.salesperson_id.receipt_book_id
            else:
                rec.receipt_book_id = False

    def action_post(self):
        res = super().action_post()

        for payment in self:

            # فقط سندات القبض من العملاء
            if payment.payment_type != "inbound":
                continue

            if payment.partner_type != "customer":
                continue

            # إذا كان السند لديه رقم بالفعل فلا ينشئ رقماً جديداً
            if payment.receipt_number:
                continue

            if not payment.salesperson_id:
                raise ValidationError(
                    "Please select a Salesperson."
                )

            # الحصول على دفتر السندات من المندوب مباشرة
            book = payment.salesperson_id.receipt_book_id

            if not book:
                raise ValidationError(
                    "The selected salesperson has no Receipt Book."
                )

            if book.next_number > book.to_number:
                raise ValidationError(
                    "Receipt Book has no remaining numbers."
                )

            # حفظ الدفتر ورقم السند
            payment.receipt_book_id = book
            payment.receipt_number = book.next_number

            # زيادة الرقم التالي
            book.next_number += 1

        return res