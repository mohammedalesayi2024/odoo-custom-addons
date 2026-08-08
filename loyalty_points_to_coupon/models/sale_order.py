# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

# عتبة النقاط التي عندها يُصدر الكوبون تلقائيًا وفوريًا
COUPON_TRIGGER_POINTS = 100.0
# قاعدة التحويل: كل 10 نقاط = 1 ريال => 100 نقطة = 10 ريال
COUPON_POINTS_PER_CURRENCY = 10.0
# الحد الأدنى لقيمة المشتريات المؤهلة لمنح نقطة واحدة
MIN_ELIGIBLE_AMOUNT = 20.0
# عدد النقاط الممنوحة لكل طلب مؤهل (نقطة واحدة ثابتة حسب السياسة الحالية،
# بغض النظر عن حجم الفاتورة طالما تجاوزت الحد الأدنى)
POINTS_PER_ELIGIBLE_ORDER = 1.0


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._apply_loyalty_earning_policy()
        return res

    def _get_loyalty_eligible_amount(self):
        """المبلغ المؤهل لاحتساب نقاط الولاء = مجموع سطور المنتجات التي:
        - ليست سطر ملاحظة/قسم (display_type)
        - ليست سطر مكافأة/عرض ناتج عن محرك الولاء (is_reward_line)
        - لا يوجد عليها أي نسبة خصم على مستوى السطر (discount == 0)
        """
        self.ensure_one()
        eligible_lines = self.order_line.filtered(
            lambda l: not l.display_type
            and not l.is_reward_line
            and not l.discount
        )
        return sum(eligible_lines.mapped("price_subtotal"))

    def _apply_loyalty_earning_policy(self):
        self.ensure_one()

        if not self.partner_id or self.partner_id.id == self.env.ref(
            "base.public_partner"
        ).id:
            return

        program = self.env.ref(
            "loyalty_points_to_coupon.loyalty_program_points_earning",
            raise_if_not_found=False,
        )
        if not program:
            return

        eligible_amount = self._get_loyalty_eligible_amount()
        if eligible_amount < MIN_ELIGIBLE_AMOUNT:
            return

        card = self.env["loyalty.card"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("program_id", "=", program.id),
            ],
            limit=1,
        )
        if not card:
            card = self.env["loyalty.card"].create(
                {
                    "partner_id": self.partner_id.id,
                    "program_id": program.id,
                    "points": 0,
                }
            )

        card.points += POINTS_PER_ELIGIBLE_ORDER
        self.message_post(
            body=_(
                "تم منح %(points)s نقطة ولاء عن هذا الطلب "
                "(المبلغ المؤهل: %(amount).2f)."
            )
            % {"points": POINTS_PER_ELIGIBLE_ORDER, "amount": eligible_amount}
        )

        # الإصدار الفوري للكوبون بمجرد بلوغ العتبة
        if card.points >= COUPON_TRIGGER_POINTS:
            card._issue_conversion_coupon(
                points_to_convert=COUPON_TRIGGER_POINTS,
                points_per_currency=COUPON_POINTS_PER_CURRENCY,
                send_notification=True,
                source_label=_("إصدار تلقائي عند بلوغ 100 نقطة"),
            )
