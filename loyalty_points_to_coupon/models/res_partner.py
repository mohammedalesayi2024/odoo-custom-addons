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
        """يفتح المعالج (Wizard) الخاص بتحويل النقاط إلى كوبون."""
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

    def _get_or_create_earning_loyalty_card(self):
        """يرجع بطاقة برنامج "نقاط الولاء (اكتساب)" الخاصة بالعميل،
        وينشئها إن لم تكن موجودة. رصيد أي بطاقة موجودة مسبقًا (مثلاً من
        اختبارات سابقة أو ترحيل بيانات) يُحافَظ عليه ويُستكمَل عليه —
        لا يُعاد تصفيره أبدًا هنا.
        """
        self.ensure_one()
        program = self.env.ref(
            "loyalty_points_to_coupon.loyalty_program_points_earning",
            raise_if_not_found=False,
        )
        if not program:
            return self.env["loyalty.card"]

        card = self.env["loyalty.card"].search(
            [("partner_id", "=", self.id), ("program_id", "=", program.id)],
            limit=1,
        )
        if not card:
            card = self.env["loyalty.card"].create(
                {"partner_id": self.id, "program_id": program.id, "points": 0}
            )
        return card

    def _grant_loyalty_points_for_order(self, eligible_amount, source_label=None):
        """منطق منح النقاط المشترك بين Sales وPOS. يُستدعى مرة واحدة فقط
        لكل طلب/فاتورة مؤكَّدة، ويتحقق تلقائيًا من عتبة إصدار الكوبون
        (من الإعدادات) ويُصدره فورًا عند بلوغها.

        كل القيم (وحدة الاحتساب، العتبة، قيمة الكوبون) تُقرأ من
        loyalty.policy.settings بدل أن تكون ثابتة بالكود، حتى يقدر
        المستخدم تعديلها من الواجهة مباشرة.
        """
        self.ensure_one()

        if self.id == self.env.ref("base.public_partner").id:
            return

        settings = self.env["loyalty.policy.settings"].get_settings()
        unit = settings.points_currency_unit or 20.0

        if eligible_amount < unit:
            return

        points_earned = int(eligible_amount // unit)
        if points_earned <= 0:
            return

        card = self._get_or_create_earning_loyalty_card()
        if not card:
            return

        card.points += points_earned
        self.message_post(
            body=_(
                "(%(source)s) تم منح %(points)s نقطة ولاء "
                "(المبلغ المؤهل: %(amount).2f، بواقع نقطة لكل %(unit)s)."
            )
            % {
                "source": source_label or _("طلب"),
                "points": points_earned,
                "amount": eligible_amount,
                "unit": unit,
            }
        )

        trigger = settings.coupon_trigger_points or 100.0
        value = settings.coupon_value_currency or 10.0
        points_per_currency = trigger / value if value else 10.0

        if card.points >= trigger:
            card._issue_conversion_coupon(
                points_to_convert=trigger,
                points_per_currency=points_per_currency,
                send_notification=True,
                source_label=_("إصدار تلقائي عند بلوغ %s نقطة") % trigger,
            )

    def action_check_and_issue_pending_coupons(self):
        """أداة "تحقق الآن" (يدوية أو عبر Cron): تفحص كل بطاقات برنامج
        الاكتساب التي رصيدها ≥ عتبة الإصدار الحالية في الإعدادات وتُصدر
        لهم كوبونًا فوريًا دون انتظار عملية بيع جديدة."""
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
                send_notification=True,
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
