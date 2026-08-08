# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from .loyalty_policy_constants import (
    COUPON_TRIGGER_POINTS,
    COUPON_POINTS_PER_CURRENCY,
    MIN_ELIGIBLE_AMOUNT,
    POINTS_PER_ELIGIBLE_ORDER,
)


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
        لكل طلب/فاتورة مؤكَّدة، ويتحقق تلقائيًا من عتبة الـ100 نقطة
        ويُصدر الكوبون فورًا عند بلوغها (سواء كان الرصيد وصل بفضل هذا
        الطلب، أو كان أصلًا مرتفعًا من رصيد سابق).
        """
        self.ensure_one()

        if self.id == self.env.ref("base.public_partner").id:
            return

        if eligible_amount < MIN_ELIGIBLE_AMOUNT:
            return

        card = self._get_or_create_earning_loyalty_card()
        if not card:
            return

        card.points += POINTS_PER_ELIGIBLE_ORDER
        self.message_post(
            body=_(
                "(%(source)s) تم منح %(points)s نقطة ولاء "
                "(المبلغ المؤهل: %(amount).2f)."
            )
            % {
                "source": source_label or _("طلب"),
                "points": POINTS_PER_ELIGIBLE_ORDER,
                "amount": eligible_amount,
            }
        )

        if card.points >= COUPON_TRIGGER_POINTS:
            card._issue_conversion_coupon(
                points_to_convert=COUPON_TRIGGER_POINTS,
                points_per_currency=COUPON_POINTS_PER_CURRENCY,
                send_notification=True,
                source_label=_("إصدار تلقائي عند بلوغ 100 نقطة"),
            )

    def action_check_and_issue_pending_coupons(self):
        """أداة "تحقق الآن" يدوية: تفحص كل بطاقات برنامج الاكتساب التي
        رصيدها الحالي ≥ 100 (مثلًا عملاء لديهم أرصدة سابقة من قبل تركيب
        الموديول أو لم يمر عليهم طلب جديد بعد بلوغ العتبة) وتُصدر لهم
        كوبونًا فوريًا دون انتظار عملية بيع جديدة.
        """
        program = self.env.ref(
            "loyalty_points_to_coupon.loyalty_program_points_earning",
            raise_if_not_found=False,
        )
        if not program:
            return

        pending_cards = self.env["loyalty.card"].search(
            [("program_id", "=", program.id), ("points", ">=", COUPON_TRIGGER_POINTS)]
        )
        issued = 0
        for card in pending_cards:
            card._issue_conversion_coupon(
                points_to_convert=COUPON_TRIGGER_POINTS,
                points_per_currency=COUPON_POINTS_PER_CURRENCY,
                send_notification=True,
                source_label=_("تصحيح/مسح دوري لأرصدة سابقة ≥ 100 نقطة"),
            )
            issued += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("تم الفحص"),
                "message": _("تم إصدار %s كوبون لعملاء وصلوا لـ100 نقطة.") % issued,
                "sticky": False,
                "type": "success" if issued else "info",
            },
        }
