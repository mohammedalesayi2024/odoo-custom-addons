# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class LoyaltyPolicySettings(models.Model):
    _name = "loyalty.policy.settings"
    _description = "إعدادات سياسة نقاط الولاء"

    name = fields.Char(default="الإعدادات الافتراضية", required=True)

    points_currency_unit = fields.Float(
        string="كل كم ريال = نقطة ولاء واحدة",
        default=20.0,
        help="مثال: 20 يعني كل 20 ريال من المبلغ المؤهل = نقطة واحدة "
        "(يُهمَل الكسر، فاتورة 103 ريال ÷ 20 = 5 نقاط).",
    )
    use_tax_included_amount = fields.Boolean(
        string="احتساب النقاط على المبلغ شامل الضريبة",
        default=False,
        help="إذا كان مفعّلاً: يُحتسب على السعر شامل الضريبة (مثال: فاتورة "
        "103 ريال شاملة الضريبة ÷ 20 = 5 نقاط). إذا كان معطّلاً (الافتراضي): "
        "يُحتسب على السعر قبل الضريبة (103 ÷ 1.15 = 89.57 ÷ 20 = 4 نقاط).",
    )
    coupon_trigger_points = fields.Float(
        string="عتبة إصدار الكوبون التلقائي (نقطة)",
        default=100.0,
    )
    coupon_value_currency = fields.Float(
        string="قيمة الكوبون الصادر عند بلوغ العتبة (ريال)",
        default=10.0,
    )
    block_coupon_with_other_discount_sales = fields.Boolean(
        string="منع استخدام الكوبون مع أي عرض/خصم آخر (Sales)",
        default=True,
        help="عند التفعيل: لن يقبل النظام تأكيد أي طلب مبيعات يحتوي على "
        "كوبون نقاط الولاء بالإضافة إلى منتج آخر عليه خصم أو عرض.",
    )
    earn_excluded_category_ids = fields.Many2many(
        "product.category",
        "loyalty_policy_earn_excluded_categ_rel",
        "settings_id",
        "category_id",
        string="فئات مستثناة من اكتساب النقاط",
        help="أي منتج ضمن هذه الفئات لا يمنح العميل نقاط ولاء أبدًا، حتى "
        "بدون خصم على السطر.",
    )
    redeem_excluded_category_ids = fields.Many2many(
        "product.category",
        "loyalty_policy_redeem_excluded_categ_rel",
        "settings_id",
        "category_id",
        string="فئات مستثناة من استخدام كوبون تحويل النقاط",
        help="مثال: البن والإكسسوارات. لن يعمل الكوبون على أي منتج ضمن "
        "هذه الفئات. يُطبَّق تلقائيًا على برنامج الكوبون عند الحفظ.",
    )

    @api.model
    def get_settings(self):
        """يرجع سجل الإعدادات الوحيد (Singleton)، وينشئه بقيم افتراضية
        إن لم يكن موجودًا بعد."""
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_redeem_categories_to_coupon_reward()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "redeem_excluded_category_ids" in vals:
            self._sync_redeem_categories_to_coupon_reward()
        return res

    def _sync_redeem_categories_to_coupon_reward(self):
        """يحدّث تلقائيًا مكافأة برنامج الكوبون بحيث تشمل كل الفئات ما
        عدا الفئات المستثناة المختارة هنا، دون الحاجة لفتح شاشة المكافأة
        يدويًا في كل مرة."""
        reward = self.env.ref(
            "loyalty_points_to_coupon.coupon_reward_loyalty_conversion",
            raise_if_not_found=False,
        )
        if not reward:
            return

        for settings in self:
            all_categories = self.env["product.category"].search([])
            included_categories = all_categories - settings.redeem_excluded_category_ids
            vals = {"discount_applicability": "specific"}
            try:
                vals["discount_product_category_id"] = [
                    (6, 0, included_categories.ids)
                ]
                reward.write(vals)
            except Exception:
                # قد يختلف اسم الحقل بين نسخ أودو - نطبّق ما أمكن على الأقل
                # ونترك تنبيهًا في سجل الأنشطة للمراجعة اليدوية إن لزم.
                reward.write({"discount_applicability": "specific"})
                self.env["ir.logging"].sudo().create(
                    {
                        "name": "loyalty_points_to_coupon",
                        "type": "server",
                        "level": "WARNING",
                        "message": (
                            "تعذّر تحديث حقل الفئات المشمولة على مكافأة "
                            "الكوبون تلقائيًا - يرجى ضبطها يدويًا من واجهة "
                            "المكافأة."
                        ),
                        "path": "loyalty_policy_settings",
                        "func": "_sync_redeem_categories_to_coupon_reward",
                        "line": "0",
                    }
                )
