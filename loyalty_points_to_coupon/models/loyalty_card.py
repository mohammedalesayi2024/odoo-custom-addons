# -*- coding: utf-8 -*-
import secrets
import string

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoyaltyCard(models.Model):
    _inherit = "loyalty.card"

    def write(self, vals):
        old_points_by_id = {}
        if "points" in vals:
            old_points_by_id = {card.id: card.points for card in self}

        res = super().write(vals)

        if "points" in vals:
            for card in self:
                card._maybe_auto_issue_coupon(old_points_by_id.get(card.id, 0.0))

        return res

    def _maybe_auto_issue_coupon(self, old_points):
        """يُصدر كوبونًا تلقائيًا فور عبور رصيد بطاقة برنامج "نقاط الولاء
        (اكتساب)" لعتبة الإصدار المحدَّدة في الإعدادات - بغض النظر عن
        مصدر إضافة النقاط (قاعدة Odoo الأصلية المرئية، تعديل يدوي، أو أي
        آلية أخرى). يعمل فقط عند "عبور" العتبة لأول مرة (من تحتها إلى
        فوقها) لتفادي التكرار.
        """
        self.ensure_one()

        program = self.env.ref(
            "loyalty_points_to_coupon.loyalty_program_points_earning",
            raise_if_not_found=False,
        )
        if not program or self.program_id.id != program.id:
            return

        settings = self.env["loyalty.policy.settings"].get_settings()
        trigger = settings.coupon_trigger_points or 100.0
        value = settings.coupon_value_currency or 10.0

        if old_points >= trigger or self.points < trigger:
            return

        points_per_currency = trigger / value if value else 10.0
        self._issue_conversion_coupon(
            points_to_convert=trigger,
            points_per_currency=points_per_currency,
            send_notification=True,
            source_label=_("إصدار تلقائي فوري عند بلوغ %s نقطة") % trigger,
        )

    def _generate_unique_coupon_code(self):
        """يولّد رمز كوبون عشوائي وآمن (غير قابل للتخمين أو التسلسل) عبر
        مكتبة secrets - المخصصة في بايثون لتوليد قيم حساسة أمنيًا
        (بعكس random العادية، القابلة للتنبؤ لو عرف أحد حالتها الداخلية).
        البادئة وطول الجزء العشوائي يُضبطان من واجهة أودو مباشرة داخل
        شاشة برنامج "نقاط الولاء (اكتساب)" ← تبويب "إعدادات الكوبون
        التلقائي" ← "شكل رمز الكوبون"، دون أي شكل ثابت مفروض من الكود.
        """
        settings = self.env["loyalty.policy.settings"].get_settings()
        prefix = settings.coupon_code_prefix or ""
        length = max(settings.coupon_code_length or 6, 4)
        alphabet = string.ascii_uppercase + string.digits

        for _attempt in range(50):
            random_part = "".join(secrets.choice(alphabet) for _ in range(length))
            code = "%s%s" % (prefix, random_part)
            if not self.search([("code", "=", code)], limit=1):
                return code

        raise UserError(
            _(
                "تعذّر توليد رمز كوبون فريد بعد عدة محاولات. يرجى زيادة "
                "طول الجزء العشوائي من الرمز من إعدادات برنامج نقاط "
                "الولاء."
            )
        )

    def _issue_conversion_coupon(
        self, points_to_convert, points_per_currency=10.0, send_notification=True,
        source_label=None,
    ):
        """يخصم points_to_convert من بطاقة self وينشئ كوبون خصم جديد بقيمة
        مكافئة على برنامج الكوبونات، ثم يرسل إشعارًا للعميل (اختياري).
        تُستخدم هذه الدالة من المعالج اليدوي ومن التحويل التلقائي عند
        بلوغ عتبة النقاط على حد سواء، لضمان نفس السلوك في الحالتين.
        """
        self.ensure_one()

        if points_to_convert <= 0:
            raise UserError(_("عدد النقاط المراد تحويلها يجب أن يكون أكبر من صفر."))
        if points_to_convert > self.points:
            raise UserError(_("رصيد النقاط غير كافٍ لإتمام عملية التحويل."))
        if not points_per_currency:
            raise UserError(_("قاعدة التحويل غير صحيحة."))

        coupon_value = points_to_convert / points_per_currency
        if coupon_value <= 0:
            raise UserError(_("قيمة الكوبون الناتجة يجب أن تكون أكبر من صفر."))

        coupon_program = self.env.ref(
            "loyalty_points_to_coupon.coupon_program_loyalty_conversion",
            raise_if_not_found=False,
        )
        if not coupon_program:
            raise UserError(_("لم يتم العثور على برنامج الكوبون."))

        # 1) خصم النقاط
        self.points -= points_to_convert

        # 2) إنشاء الكوبون
        new_coupon = self.env["loyalty.card"].create(
            {
                "partner_id": self.partner_id.id,
                "program_id": coupon_program.id,
                "points": coupon_value,
                "code": self._generate_unique_coupon_code(),
            }
        )

        # 3) ملاحظة على العميل
        if self.partner_id:
            label = source_label or _("تحويل يدوي")
            self.partner_id.message_post(
                body=_(
                    "(%(label)s) تم تحويل %(points)s نقطة إلى كوبون بقيمة "
                    "%(value).2f - رمز الكوبون: %(code)s"
                )
                % {
                    "label": label,
                    "points": points_to_convert,
                    "value": coupon_value,
                    "code": new_coupon.code,
                }
            )

        # 4) إرسال إشعار
        if send_notification:
            template = self.env.ref(
                "loyalty_points_to_coupon.mail_template_coupon_sent",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(new_coupon.id, force_send=True)

        return new_coupon
