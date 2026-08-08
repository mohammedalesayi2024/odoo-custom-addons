# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._warn_if_coupon_combined_with_discount_pos()
        return orders

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
