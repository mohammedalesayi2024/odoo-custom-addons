# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self._check_coupon_combination_policy()
        res = super().action_confirm()
        for order in self:
            order._apply_loyalty_earning_policy()
        return res

    def _check_coupon_combination_policy(self):
        """يمنع تأكيد الطلب إذا كان فيه كوبون تحويل نقاط الولاء بالإضافة
        إلى منتج آخر عليه خصم/عرض في نفس الطلب، إذا كان الإعداد مفعّلاً."""
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

    def _get_loyalty_eligible_amount(self):
        """المبلغ المؤهل لاحتساب نقاط الولاء = مجموع سطور المنتجات التي:
        - ليست سطر ملاحظة/قسم (display_type)
        - ليست سطر مكافأة/عرض ناتج عن محرك الولاء (is_reward_line)
        - لا يوجد عليها أي نسبة خصم على مستوى السطر (discount == 0)
        - ليست ضمن فئة مستثناة من الاكتساب (حسب الإعدادات)
        القيمة المستخدمة (شامل الضريبة أو لا) تُحدَّد من الإعدادات أيضًا.
        """
        self.ensure_one()
        settings = self.env["loyalty.policy.settings"].get_settings()
        excluded_categ_ids = settings.earn_excluded_category_ids.ids

        eligible_lines = self.order_line.filtered(
            lambda l: not l.display_type
            and not l.is_reward_line
            and not l.discount
            and l.product_id.categ_id.id not in excluded_categ_ids
        )
        amount_field = "price_total" if settings.use_tax_included_amount else "price_subtotal"
        return sum(eligible_lines.mapped(amount_field))

    def _apply_loyalty_earning_policy(self):
        self.ensure_one()
        if not self.partner_id:
            return
        eligible_amount = self._get_loyalty_eligible_amount()
        self.partner_id._grant_loyalty_points_for_order(
            eligible_amount, source_label=_("طلب مبيعات %s") % self.name
        )
