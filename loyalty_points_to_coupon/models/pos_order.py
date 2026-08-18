# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._check_coupon_minimum_order_policy()
        orders._warn_if_coupon_combined_with_discount_pos()
        return orders

    def _check_coupon_minimum_order_policy(self):
        """يمنع إتمام الطلب كليًا (خطأ صريح يوقف الحفظ/الدفع) إذا كان
        إجمالي الطلب قبل خصم الكوبون أقل من قيمة الكوبون نفسها - سياسة
        "منع كلي" بدون استخدام جزئي. على عكس تحذير دمج الخصومات، هذا
        الفحص يمنع فعليًا لأنه يحدث وقت إنشاء سجل الطلب في create()،
        قبل تأكيد الدفع نهائيًا في واجهة نقطة البيع."""
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
            reward_lines = order.lines.filtered(
                lambda l: l.is_reward_line
                and l.reward_id
                and l.reward_id.program_id.id == coupon_program.id
            )
            if not reward_lines:
                continue

            other_lines = order.lines - reward_lines
            base_amount = sum(other_lines.mapped("price_subtotal_incl"))

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

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") in ("paid", "done", "invoiced"):
            self._warn_if_coupon_combined_with_discount_pos()
        return res

    def _warn_if_coupon_combined_with_discount_pos(self):
        """POS لا يمكن حجب الدفع مباشرة من الخلفية (الدفع يتم بواجهة
        الجافاسكربت قبل وصول الطلب هنا)، لذلك نكتفي بتحذير مسجَّل على
        الطلب لمراجعة الموظف/الإدارة، بدل منع صريح كما في Sales.
        (اكتساب النقاط نفسه أصبح يعتمد بالكامل على قاعدة Odoo الأصلية)."""
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
                for line in order.lines
            )
            if not has_our_coupon:
                continue

            other_discounted = order.lines.filtered(
                lambda l: not l.is_reward_line and l.discount > 0
            )
            if other_discounted:
                order.message_post(
                    body=_(
                        "⚠️ تنبيه: تم إتمام هذا الطلب بكوبون نقاط ولاء "
                        "مع منتج آخر عليه خصم/عرض في نفس الوقت، وهذا "
                        "مخالف لسياسة الشركة. يرجى مراجعة الطلب."
                    )
                )
