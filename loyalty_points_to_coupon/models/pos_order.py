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
        return orders

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") in ("paid", "done", "invoiced"):
            self._apply_loyalty_earning_policy_pos()
        return res

    def _get_loyalty_eligible_amount_pos(self):
        """نفس منطق الاستثناء المستخدم في sale.order: تُستبعد سطور
        المكافآت/العروض (is_reward_line) وأي سطر عليه خصم (discount > 0).
        """
        self.ensure_one()
        eligible_lines = self.lines.filtered(
            lambda l: not l.is_reward_line and not l.discount
        )
        return sum(eligible_lines.mapped("price_subtotal"))

    def _apply_loyalty_earning_policy_pos(self):
        for order in self:
            if order.loyalty_points_granted:
                continue
            # نمنح النقاط فقط عند اكتمال الدفع فعليًا
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
