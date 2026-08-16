# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    loyalty_card_ids = fields.One2many(
        "loyalty.card", "partner_id", string="بطاقات الولاء"
    )
    total_loyalty_points = fields.Float(
        string="إجمالي نقاط الولاء",
        compute="_compute_total_loyalty_points",
    )

    @api.depends("loyalty_card_ids", "loyalty_card_ids.points")
    def _compute_total_loyalty_points(self):
        for partner in self:
            cards = partner.loyalty_card_ids.filtered(
                lambda c: c.program_id.program_type == "loyalty"
            )
            partner.total_loyalty_points = sum(cards.mapped("points"))

    def action_open_point_to_coupon_wizard(self):
        """يفتح المعالج (Wizard) الخاص بتحويل النقاط إلى كوبون يدويًا."""
        self.ensure_one()
        loyalty_cards = self.loyalty_card_ids.filtered(
            lambda c: c.program_id.program_type == "loyalty" and c.points > 0
        )
        return {
            "type": "ir.actions.act_window",
            "name": "تحويل نقاط الولاء إلى كوبون",
            "res_model": "loyalty.point.to.coupon.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_loyalty_card_id": loyalty_cards[:1].id,
            },
        }

    def action_check_and_issue_pending_coupons(self):
        """شبكة أمان (يدوية أو عبر Cron): تفحص كل بطاقات برنامج الاكتساب
        التي رصيدها ≥ عتبة الإصدار الحالية في الإعدادات وتُصدر لهم كوبونًا
        فوريًا. مفيدة للحالات النادرة اللي ما تلتقطها مراقبة loyalty.card
        مباشرة (مثلًا استيراد بيانات عبر SQL مباشر يتجاوز ORM)."""
        program = self.env.ref(
            "loyalty_points_to_coupon.loyalty_program_points_earning",
            raise_if_not_found=False,
        )
        if not program:
            return

        settings = self.env["loyalty.policy.settings"].get_settings()
        trigger = settings.coupon_trigger_points or 100.0
        value = settings.coupon_value_currency or 10.0
        points_per_currency = trigger / value if value else 10.0

        pending_cards = self.env["loyalty.card"].search(
            [("program_id", "=", program.id), ("points", ">=", trigger)]
        )
        issued = 0
        for card in pending_cards:
            card._issue_conversion_coupon(
                points_to_convert=trigger,
                points_per_currency=points_per_currency,
                send_notification=settings.auto_send_coupon_notification,
                source_label=_("تصحيح/مسح دوري لأرصدة سابقة ≥ %s نقطة") % trigger,
            )
            issued += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("تم الفحص"),
                "message": _("تم إصدار %s كوبون لعملاء وصلوا للعتبة.") % issued,
                "sticky": False,
                "type": "success" if issued else "info",
            },
        }
