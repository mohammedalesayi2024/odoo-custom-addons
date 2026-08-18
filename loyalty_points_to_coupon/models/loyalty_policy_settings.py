# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoyaltyPolicySettings(models.Model):
    _name = "loyalty.policy.settings"
    _description = "إعدادات سياسة نقاط الولاء"

    name = fields.Char(default="الإعدادات الافتراضية", required=True)

    # ملاحظة: احتساب اكتساب النقاط نفسه (كم ريال = كم نقطة) أصبح يُضبط
    # مباشرة من قاعدة (Rule) مرئية وقابلة للتعديل في واجهة أودو، داخل
    # برنامج "نقاط الولاء (اكتساب)" → تبويب "القواعد والمكافآت". هذه
    # الشاشة تبقى فقط للإعدادات التي لا يوفرها أودو أصلًا.

    coupon_trigger_points = fields.Float(
        string="عتبة إصدار الكوبون التلقائي (نقطة)",
        default=100.0,
        help="بمجرد وصول/تجاوز رصيد العميل لهذا الرقم، يُصدر كوبون فورًا "
        "تلقائيًا، بغض النظر عن مصدر النقاط (قاعدة أودو أو تعديل يدوي).",
    )
    coupon_value_currency = fields.Float(
        string="قيمة الكوبون الصادر عند بلوغ العتبة (ريال)",
        default=10.0,
    )
    block_coupon_with_other_discount_sales = fields.Boolean(
        string="منع استخدام الكوبون مع أي عرض/خصم آخر (Sales)",
        default=True,
        help="عند التفعيل: لن يقبل النظام تأكيد أي طلب مبيعات يحتوي على "
        "كوبون نقاط الولاء بالإضافة إلى منتج آخر عليه خصم أو عرض. في "
        "نقطة البيع (POS) يُسجَّل تحذير بعد إتمام الطلب بدل المنع الفوري.",
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
    coupon_code_prefix = fields.Char(
        string="بادئة رمز الكوبون",
        default="LOY-",
        help="تُضاف في بداية كل رمز كوبون. اتركها فارغة لعدم استخدام "
        "بادئة.",
    )
    coupon_code_length = fields.Integer(
        string="طول الجزء العشوائي من الرمز",
        default=6,
        help="عدد الخانات العشوائية (حروف وأرقام) بعد البادئة. كل ما "
        "زاد الرقم كل ما قلّ احتمال التخمين أو التكرار. الحد الأدنى "
        "الموصى به: 6.",
    )
    auto_send_coupon_notification = fields.Boolean(
        string="إرسال إشعار الكوبون تلقائيًا عبر البريد الإلكتروني",
        default=True,
        help="مفتاح تشغيل/إيقاف: عند التفعيل، بمجرد إصدار كوبون تلقائي "
        "(عند بلوغ العميل عتبة النقاط) يُرسل له بريد إلكتروني فوري "
        "يخبره بذلك. عند التعطيل، يُصدر الكوبون كالمعتاد لكن بدون أي "
        "إرسال تلقائي - وتقدر ترسله يدويًا لاحقًا من شاشة الكوبونات "
        "(حدد البطاقة ← زر الإجراءات ← 'إرسال إشعار الكوبون للعميل').",
    )
    block_coupon_below_value = fields.Boolean(
        string="منع استخدام الكوبون إذا كانت الفاتورة أقل من قيمته",
        default=True,
        help="عند التفعيل (سياسة منع كلي): لن يُقبل استخدام كوبون تحويل "
        "نقاط الولاء إطلاقًا إذا كان إجمالي الفاتورة (قبل تطبيق "
        "الكوبون) أقل من قيمة الكوبون نفسها (مثال: كوبون بقيمة 10 "
        "ريال لن يعمل على فاتورة قيمتها 5 ريال). هذا يمنع فقدان أي "
        "جزء من قيمة الكوبون بسبب فاتورة صغيرة. يظهر خطأ صريح يمنع "
        "إتمام البيع في كل من المبيعات ونقطة البيع.",
    )

    @api.constrains("coupon_code_length")
    def _check_coupon_code_length(self):
        for rec in self:
            if rec.coupon_code_length < 4:
                raise ValidationError(
                    _(
                        "طول الجزء العشوائي من رمز الكوبون يجب ألا يقل "
                        "عن 4 خانات، حفاظًا على أمان الرمز وصعوبة "
                        "تخمينه."
                    )
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
        """يحدّث تلقائيًا مكافأة برنامج الكوبون بحيث تشمل كل المنتجات ما
        عدا المنتجات ضمن الفئات المستثناة المختارة هنا، دون الحاجة لفتح
        شاشة المكافأة يدويًا في كل مرة، وبدون سرد آلاف المنتجات في تلك
        الشاشة.

        الآلية: نستخدم علامة تصنيف واحدة ثابتة (product.tag) نديرها
        بالكامل تلقائيًا - تُضاف لكل منتج مؤهل وتُزال من غيره في كل
        مرة تتغيّر فيها الفئات المستثناة، ثم نربط هذه العلامة الواحدة
        بحقل "علامات تصنيف المنتجات المشمولة في الخصم" على المكافأة.
        هذا يعمل بنفس الطريقة على كل نسخ أودو بغض النظر عن نوع الحقل
        (Many2one أو Many2many)، لأننا نكتب علامة واحدة فقط، ويبقى حجم
        شاشة المكافأة نظيفًا مهما كان عدد المنتجات في الكتالوج."""
        reward = self.env.ref(
            "loyalty_points_to_coupon.coupon_reward_loyalty_conversion",
            raise_if_not_found=False,
        )
        eligibility_tag = self.env.ref(
            "loyalty_points_to_coupon.product_tag_loyalty_coupon_eligible",
            raise_if_not_found=False,
        )
        if not reward or not eligibility_tag:
            return

        reward_fields = self.env["loyalty.reward"]._fields
        tag_field = reward_fields.get("discount_product_tag_id")
        categ_field = reward_fields.get("discount_product_category_id")

        if not tag_field:
            # احتياط نادر: نسخة أودو بدون حقل التاق على المكافأة إطلاقًا.
            self._sync_via_category_or_product_fallback(reward, categ_field)
            return

        Product = self.env["product.product"]

        for settings in self:
            excluded = settings.redeem_excluded_category_ids

            if not excluded:
                # ما فيه أي استثناء - أبسط وأخف حل: الخصم على الطلب كامل،
                # وتُمسح العلامة من الجميع (غير مستخدمة في هذي الحالة).
                Product.search([("product_tag_ids", "in", eligibility_tag.id)]).write(
                    {"product_tag_ids": [(3, eligibility_tag.id)]}
                )
                try:
                    reward.write({"discount_applicability": "order"})
                except Exception:
                    self._log_sync_warning()
                continue

            excluded_with_children = self.env["product.category"].search(
                [("id", "child_of", excluded.ids)]
            )
            all_tagged = Product.search(
                [("product_tag_ids", "in", eligibility_tag.id)]
            )
            eligible = Product.search(
                [("categ_id", "not in", excluded_with_children.ids)]
            )
            no_longer_eligible = all_tagged - eligible
            newly_eligible = eligible - all_tagged

            # عمليتان دفعة واحدة (Bulk) بدل المرور على كل منتج لحاله -
            # سريعتان حتى مع آلاف المنتجات.
            if no_longer_eligible:
                no_longer_eligible.write({"product_tag_ids": [(3, eligibility_tag.id)]})
            if newly_eligible:
                newly_eligible.write({"product_tag_ids": [(4, eligibility_tag.id)]})

            vals = {"discount_applicability": "specific"}
            if tag_field:
                vals["discount_product_tag_id"] = (
                    [(6, 0, [eligibility_tag.id])]
                    if tag_field.type == "many2many"
                    else eligibility_tag.id
                )
            if categ_field:
                vals["discount_product_category_id"] = (
                    [(5, 0, 0)] if categ_field.type == "many2many" else False
                )
            vals["discount_product_ids"] = [(5, 0, 0)]

            try:
                reward.write(vals)
            except Exception:
                self._log_sync_warning()

    def _sync_via_category_or_product_fallback(self, reward, categ_field):
        """مسار احتياطي نادر جدًا، يُستخدم فقط لو نسخة أودو ما فيها
        حقل علامات التصنيف (discount_product_tag_id) على المكافأة
        إطلاقًا."""
        for settings in self:
            excluded = settings.redeem_excluded_category_ids
            if not excluded:
                try:
                    reward.write({"discount_applicability": "order"})
                except Exception:
                    self._log_sync_warning()
                continue

            vals = {"discount_applicability": "specific"}
            if categ_field and categ_field.type == "many2many":
                all_categories = self.env["product.category"].search([])
                included_categories = all_categories - excluded
                vals["discount_product_category_id"] = [
                    (6, 0, included_categories.ids)
                ]
            else:
                excluded_with_children = self.env["product.category"].search(
                    [("id", "child_of", excluded.ids)]
                )
                eligible_products = self.env["product.product"].search(
                    [("categ_id", "not in", excluded_with_children.ids)]
                )
                vals["discount_product_ids"] = [(6, 0, eligible_products.ids)]

            try:
                reward.write(vals)
            except Exception:
                self._log_sync_warning()

    def _log_sync_warning(self):
        self.env["ir.logging"].sudo().create(
            {
                "name": "loyalty_points_to_coupon",
                "type": "server",
                "level": "WARNING",
                "message": (
                    "تعذّر تحديث نطاق منتجات مكافأة الكوبون تلقائيًا - "
                    "يرجى ضبطها يدويًا من واجهة المكافأة."
                ),
                "path": "loyalty_policy_settings",
                "func": "_sync_redeem_categories_to_coupon_reward",
                "line": "0",
            }
        )
