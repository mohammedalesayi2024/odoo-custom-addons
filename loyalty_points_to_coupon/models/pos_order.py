# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = "pos.order"

    loyalty_points_granted = fields.Boolean(
        string="تم منح نقاط الولاء عن هذا الطلب",
        default=False,
        copy=False,
        help="يمنع منح نفس النقاط أكثر من مرة لنفس طلب POS "
        "(مثلاً عند إعادة الحفظ أو المزامنة).",
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._apply_loyalty_earning_policy_pos()
        orders._warn_if_coupon_combined_with_discount_pos()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") in ("paid", "done", "invoiced"):
            self._apply_loyalty_earning_policy_pos()
            self._warn_if_coupon_combined_with_discount_pos()
        return res

    def _get_loyalty_eligible_amount_pos(self):
        """نفس منطق sale.order: تُستبعد سطور المكافآت/العروض، وأي سطر
        عليه خصم، وأي منتج ضمن فئة مستثناة من الاكتساب حسب الإعدادات.
        القيمة (شامل الضريبة أو لا) تُحدَّد من نفس الإعدادات."""
        self.ensure_one()
        settings = self.env["loyalty.policy.settings"].get_settings()
        excluded_categ_ids = settings.earn_excluded_category_ids.ids

        eligible_lines = self.lines.filtered(
            lambda l: not l.is_reward_line
            and not l.discount
            and l.product_id.categ_id.id not in excluded_categ_ids
        )
        amount_field = (
            "price_subtotal_incl" if settings.use_tax_included_amount else "price_subtotal"
        )
        return sum(eligible_lines.mapped(amount_field))

    def _apply_loyalty_earning_policy_pos(self):
        for order in self:
            if order.loyalty_points_granted:
                continue
            if order.state not in ("paid", "done", "invoiced"):
                continue
            if not order.partner_id:
                continue

            eligible_amount = order._get_loyalty_eligible_amount_pos()
            order.partner_id._grant_loyalty_points_for_order(
                eligible_amount,
                source_label=_("طلب نقطة بيع %s") % (order.name or order.pos_reference or ""),
            )
            order.loyalty_points_granted = True

    def _warn_if_coupon_combined_with_discount_pos(self):
        """POS لا يمكن حجب الدفع مباشرة من الخلفية (الدفع يتم بواجهة
        الجافاسكربت قبل وصول الطلب هنا)، لذلك نكتفي بتحذير مسجَّل على
        الطلب لمراجعة الموظف/الإدارة، بدل منع صريح كما في Sales."""
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
