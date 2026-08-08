# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


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
        if not self.partner_id:
            return
        eligible_amount = self._get_loyalty_eligible_amount()
        self.partner_id._grant_loyalty_points_for_order(
            eligible_amount, source_label=_("طلب مبيعات %s") % self.name
        )
