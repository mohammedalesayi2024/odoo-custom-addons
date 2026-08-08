# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoyaltyPointToCouponWizard(models.TransientModel):
    _name = "loyalty.point.to.coupon.wizard"
    _description = "تحويل نقاط الولاء إلى كوبون"

    partner_id = fields.Many2one(
        "res.partner", string="العميل", required=True
    )
    loyalty_card_id = fields.Many2one(
        "loyalty.card",
        string="بطاقة الولاء",
        required=True,
        domain="[('partner_id', '=', partner_id), ('program_id.program_type', '=', 'loyalty')]",
    )
    current_points = fields.Float(
        string="رصيد النقاط الحالي",
        related="loyalty_card_id.points",
        readonly=True,
    )
    points_to_convert = fields.Float(
        string="النقاط المراد تحويلها", required=True
    )
    points_per_currency = fields.Float(
        string="عدد النقاط مقابل كل وحدة نقدية",
        default=10.0,
        help="مثال: إذا كانت القيمة 10، فهذا يعني أن كل 10 نقاط = 1 ريال.",
    )
    coupon_value = fields.Float(
        string="قيمة الكوبون",
        compute="_compute_coupon_value",
        store=True,
    )
    send_notification = fields.Boolean(
        string="إرسال إشعار للعميل تلقائيًا عبر البريد الإلكتروني",
        default=True,
    )

    @api.depends("points_to_convert", "points_per_currency")
    def _compute_coupon_value(self):
        for rec in self:
            if rec.points_per_currency:
                rec.coupon_value = rec.points_to_convert / rec.points_per_currency
            else:
                rec.coupon_value = 0.0

    def action_confirm(self):
        self.ensure_one()

        if self.points_to_convert > self.loyalty_card_id.points:
            raise UserError(_("رصيد النقاط غير كافٍ لإتمام عملية التحويل."))

        new_coupon = self.loyalty_card_id._issue_conversion_coupon(
            points_to_convert=self.points_to_convert,
            points_per_currency=self.points_per_currency,
            send_notification=self.send_notification,
            source_label=_("تحويل يدوي من قبل الموظف"),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("تم إنشاء الكوبون بنجاح"),
                "message": _("رمز الكوبون: %s - القيمة: %.2f")
                % (new_coupon.code, new_coupon.points),
                "sticky": False,
                "type": "success",
            },
        }
