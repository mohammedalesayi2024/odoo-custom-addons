# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    # حقل تقني: يحدد ما إذا كان هذا السجل هو برنامج "نقاط الولاء (اكتساب)"
    # تحديدًا، لإظهار مجموعة إعدادات الكوبون التلقائي فقط داخله وليس في
    # بقية برامج الولاء/الكوبونات الأخرى.
    is_points_earning_program = fields.Boolean(
        string="برنامج اكتساب النقاط الرئيسي",
        compute="_compute_is_points_earning_program",
    )

    # الحقول التالية تُقرأ وتُكتب مباشرة من/إلى سجل loyalty.policy.settings
    # الوحيد (Singleton)، بحيث تظهر هنا كأنها جزء أصيل من شاشة البرنامج،
    # بينما التخزين الفعلي يبقى في نفس المكان القديم دون أي تغيير على
    # بقية الكود (loyalty_card.py, sale_order.py, pos_order.py...).
    coupon_trigger_points = fields.Float(
        string="عتبة إصدار الكوبون التلقائي (نقطة)",
        compute="_compute_policy_settings_fields",
        inverse="_inverse_coupon_trigger_points",
        help="بمجرد وصول/تجاوز رصيد العميل لهذا الرقم، يُصدر كوبون فورًا "
        "تلقائيًا، بغض النظر عن مصدر النقاط (قاعدة أودو أو تعديل يدوي).",
    )
    coupon_value_currency = fields.Float(
        string="قيمة الكوبون الصادر عند بلوغ العتبة (ريال)",
        compute="_compute_policy_settings_fields",
        inverse="_inverse_coupon_value_currency",
    )
    redeem_excluded_category_ids = fields.Many2many(
        "product.category",
        string="فئات مستثناة من استخدام كوبون تحويل النقاط",
        compute="_compute_policy_settings_fields",
        inverse="_inverse_redeem_excluded_category_ids",
        help="مثال: البن والإكسسوارات. لن يعمل الكوبون على أي منتج ضمن "
        "هذه الفئات. يُطبَّق تلقائيًا على برنامج الكوبون عند الحفظ.",
    )
    block_coupon_with_other_discount_sales = fields.Boolean(
        string="منع استخدام الكوبون مع أي عرض/خصم آخر (Sales)",
        compute="_compute_policy_settings_fields",
        inverse="_inverse_block_coupon_with_other_discount_sales",
        help="عند التفعيل: لن يقبل النظام تأكيد أي طلب مبيعات يحتوي على "
        "كوبون نقاط الولاء بالإضافة إلى منتج آخر عليه خصم أو عرض. في "
        "نقطة البيع (POS) يُسجَّل تحذير بعد إتمام الطلب بدل المنع الفوري.",
    )
    coupon_code_prefix = fields.Char(
        string="بادئة رمز الكوبون",
        compute="_compute_policy_settings_fields",
        inverse="_inverse_coupon_code_prefix",
        help="تُضاف في بداية كل رمز كوبون. اتركها فارغة لعدم استخدام "
        "بادئة.",
    )
    coupon_code_length = fields.Integer(
        string="طول الجزء العشوائي من الرمز",
        compute="_compute_policy_settings_fields",
        inverse="_inverse_coupon_code_length",
        help="عدد الخانات العشوائية (حروف وأرقام) بعد البادئة. كل ما "
        "زاد الرقم كل ما قلّ احتمال التخمين أو التكرار. الحد الأدنى: 4.",
    )

    def _compute_is_points_earning_program(self):
        program = self.env.ref(
            "loyalty_points_to_coupon.loyalty_program_points_earning",
            raise_if_not_found=False,
        )
        for rec in self:
            rec.is_points_earning_program = bool(program) and rec.id == program.id

    def _compute_policy_settings_fields(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            rec.coupon_trigger_points = settings.coupon_trigger_points
            rec.coupon_value_currency = settings.coupon_value_currency
            rec.redeem_excluded_category_ids = settings.redeem_excluded_category_ids
            rec.block_coupon_with_other_discount_sales = (
                settings.block_coupon_with_other_discount_sales
            )
            rec.coupon_code_prefix = settings.coupon_code_prefix
            rec.coupon_code_length = settings.coupon_code_length

    def _inverse_coupon_trigger_points(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            if rec.is_points_earning_program:
                settings.coupon_trigger_points = rec.coupon_trigger_points

    def _inverse_coupon_value_currency(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            if rec.is_points_earning_program:
                settings.coupon_value_currency = rec.coupon_value_currency

    def _inverse_redeem_excluded_category_ids(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            if rec.is_points_earning_program:
                settings.redeem_excluded_category_ids = [
                    (6, 0, rec.redeem_excluded_category_ids.ids)
                ]

    def _inverse_block_coupon_with_other_discount_sales(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            if rec.is_points_earning_program:
                settings.block_coupon_with_other_discount_sales = (
                    rec.block_coupon_with_other_discount_sales
                )

    def _inverse_coupon_code_prefix(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            if rec.is_points_earning_program:
                settings.coupon_code_prefix = rec.coupon_code_prefix

    def _inverse_coupon_code_length(self):
        settings = self.env["loyalty.policy.settings"].get_settings()
        for rec in self:
            if rec.is_points_earning_program:
                settings.coupon_code_length = rec.coupon_code_length
