# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self._check_coupon_combination_policy()
        self._check_coupon_minimum_order_policy()
        return super().action_confirm()

    def _check_coupon_minimum_order_policy(self):
        """يمنع تأكيد الطلب كليًا إذا كان إجمالي الطلب (قبل خصم
        الكوبون) أقل من قيمة الكوبون نفسها - سياسة "منع كلي" بدون
        استخدام جزئي، لتجنّب فقدان أي جزء من قيمة الكوبون."""
        settings = self.env["loyalty.policy.settings"].get_settings()
        if not settings.block_coupon_below_value:
            return

        coupon_program = self.env.ref(
            "loyalty_points_to_coupon.coupon_program_loyalty_conversion",
            raise_if_not_found=False,
        )
        if not coupon_program:
            return

        for order in self:
            reward_lines = order.order_line.filtered(
                lambda l: l.is_reward_line
                and l.reward_id
                and l.reward_id.program_id.id == coupon_program.id
            )
            if not reward_lines:
                continue

            other_lines = order.order_line - reward_lines
            base_amount = sum(other_lines.mapped("price_total"))

            if base_amount < settings.coupon_value_currency:
                raise UserError(
                    _(
                        "لا يمكن استخدام هذا الكوبون: إجمالي الفاتورة "
                        "(%(base)s) أقل من قيمة الكوبون (%(coupon)s). "
                        "يرجى إضافة منتجات أكثر أو استخدام الكوبون في "
                        "طلب لاحق."
                    )
                    % {
                        "base": "%.2f" % base_amount,
                        "coupon": "%.2f" % settings.coupon_value_currency,
                    }
                )

    def _check_coupon_combination_policy(self):
        """يمنع تأكيد الطلب إذا كان فيه كوبون تحويل نقاط الولاء بالإضافة
        إلى منتج آخر عليه خصم/عرض في نفس الطلب، إذا كان الإعداد مفعّلاً.
        (اكتساب النقاط نفسه أصبح يعتمد بالكامل على قاعدة Odoo الأصلية
        المُعرَّفة يدويًا في برنامج "نقاط الولاء (اكتساب)")."""
        settings = self.env["loyalty.policy.settings"].get_settings()
        if not settings.block_coupon_with_other_discount_sales:
            return

        coupon_program = self.env.ref(
            "loyalty_points_to_coupon.coupon_program_loyalty_conversion",
            raise_if_not_found=False,
        )
        if not coupon_program:
            return

        for order in self:
            has_our_coupon = any(
                line.is_reward_line
                and line.reward_id
                and line.reward_id.program_id.id == coupon_program.id
                for line in order.order_line
            )
            if not has_our_coupon:
                continue

            other_discounted = order.order_line.filtered(
                lambda l: not l.is_reward_line and l.discount > 0
            )
            if other_discounted:
                raise UserError(
                    _(
                        "لا يمكن استخدام كوبون نقاط الولاء مع أي منتج آخر "
                        "عليه خصم أو عرض في نفس الطلب. يرجى إزالة الخصم أو "
                        "الكوبون أولًا."
                    )
                )
