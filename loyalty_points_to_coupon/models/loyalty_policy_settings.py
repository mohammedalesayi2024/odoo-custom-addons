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
        """يحدّث تلقائيًا مكافأة برنامج الكوبون بحيث تشمل كل الفئات ما
        عدا الفئات المستثناة المختارة هنا، دون الحاجة لفتح شاشة المكافأة
        يدويًا في كل مرة.

        ملاحظة هامة: لا نترك المكافأة أبدًا بحالة discount_applicability
        = 'specific' بدون أن يكون حقل الفئات فعليًا مضبوطًا بالقيم
        الصحيحة، لأن ذلك يعني عمليًا (بحسب سلوك أودو) أن الخصم يُطبَّق
        على كل شيء بلا أي استثناء - وهو أخطر من عدم التقييد أصلاً لأنه
        يبدو مقيّدًا في الواجهة بينما هو غير ذلك فعليًا."""
        reward = self.env.ref(
            "loyalty_points_to_coupon.coupon_reward_loyalty_conversion",
            raise_if_not_found=False,
        )
        if not reward:
            return

        category_field = reward._fields.get("discount_product_category_id")

        for settings in self:
            all_categories = self.env["product.category"].search([])
            included_categories = (
                all_categories - settings.redeem_excluded_category_ids
            )
            error_message = None

            if not settings.redeem_excluded_category_ids:
                # لا يوجد استثناء مطلوب أصلاً - الخصم على كامل الطلب،
                # وهذه الحالة الوحيدة الآمنة لاستخدام discount_applicability
                # = 'order' بدون قيود فئات.
                reward.write({"discount_applicability": "order"})
                continue

            if category_field is None:
                error_message = (
                    "الحقل discount_product_category_id غير موجود في "
                    "موديل loyalty.reward بهذا الإصدار من أودو - لا يمكن "
                    "تطبيق استثناء الفئات تلقائيًا."
                )
            elif category_field.type == "many2many":
                try:
                    reward.write(
                        {
                            "discount_applicability": "specific",
                            "discount_product_category_id": [
                                (6, 0, included_categories.ids)
                            ],
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    error_message = f"فشل الكتابة على الحقل (many2many): {exc}"
            elif category_field.type == "many2one":
                # حقل بأودو يقبل فئة واحدة فقط، لا يمكن معه تنفيذ منطق
                # "كل الفئات ما عدا المستثناة" حين يكون عدد الفئات
                # المتبقية أكثر من واحدة.
                if len(included_categories) == 1:
                    try:
                        reward.write(
                            {
                                "discount_applicability": "specific",
                                "discount_product_category_id": included_categories.id,
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        error_message = f"فشل الكتابة على الحقل (many2one): {exc}"
                else:
                    error_message = (
                        "discount_product_category_id هو حقل Many2one في "
                        "هذا الإصدار (فئة واحدة فقط)، ولا يدعم استثناء "
                        "فئة واحدة أو أكثر مع بقاء أكثر من فئة مسموحة. "
                        "يلزم حل بديل (فحص يدوي في الكود بدل الاعتماد "
                        "على هذا الحقل الأصلي)."
                    )
            else:
                error_message = (
                    f"نوع حقل غير متوقع: {category_field.type}"
                )

            if error_message:
                # حالة آمنة: لا نُبقي المكافأة 'specific' بلا قيود فعلية.
                # الأفضل تعطيل الخصم مؤقتًا عن الفئات كلها (بدل فتحه
                # للجميع) وتنبيه المدير ليتدخل يدويًا.
                reward.write(
                    {
                        "discount_applicability": "specific",
                        "discount_product_category_id": [(6, 0, [])]
                        if category_field is not None
                        and category_field.type == "many2many"
                        else False,
                    }
                )
                self.env["ir.logging"].sudo().create(
                    {
                        "name": "loyalty_points_to_coupon",
                        "type": "server",
                        "level": "WARNING",
                        "message": (
                            "تعذّر تحديث حقل الفئات المشمولة على مكافأة "
                            "الكوبون تلقائيًا، وتم تعطيل الكوبون مؤقتًا "
                            "(لن يُطبَّق على أي منتج) لحين الضبط اليدوي، "
                            "بدل تركه يعمل بلا استثناء. السبب: "
                            + error_message
                        ),
                        "path": "loyalty_policy_settings",
                        "func": "_sync_redeem_categories_to_coupon_reward",
                        "line": "0",
                    }
                )
