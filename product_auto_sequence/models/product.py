from odoo import models, fields, api
from odoo.exceptions import ValidationError

# =========================
# Brand Model
# =========================
class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'

    name = fields.Char(string="Brand Name", required=True)
    shortcut = fields.Char(string="Brand Shortcut")

    def unlink(self):
        for rec in self:
            products = self.env['product.template'].search([
                ('brand_id', '=', rec.id)
            ], limit=1)

            if products:
                raise ValidationError(
                    "❌ لا يمكن حذف هذا البراند لأنه مرتبط بمنتجات"
                )

        return super().unlink()
# =========================
# Extend Product Category
# =========================
class ProductCategory(models.Model):
    _inherit = 'product.category'

    shortcut = fields.Char(string="Category Shortcut")


# =========================
# Extend Product Template
# =========================
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_sequence = fields.Char(
        string="Product Sequence",
        copy=False
    )

    brand_id = fields.Many2one('product.brand', string="Brand" ,ondelete='restrict')

    # ✅ هذا المكان الصحيح
    @api.constrains('product_sequence')
    def _check_unique_product_sequence(self):
        for rec in self:
            if rec.product_sequence:
                existing = self.search([
                    ('product_sequence', '=', rec.product_sequence),
                    ('id', '!=', rec.id)
                ], limit=1)

                if existing:
                    raise ValidationError("⚠️ Product Sequence must be unique!")

    @api.model
    def create(self, vals):
        if not vals.get('product_sequence'):
            seq = self.env['ir.sequence'].next_by_code('product.sequence')
            vals['product_sequence'] = seq or '0000'

        record = super().create(vals)
        record._update_internal_code()
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._update_internal_code()
        return res

    def _update_internal_code(self):
        for rec in self:
            category_short = rec.categ_id.shortcut or ""
            brand_short = rec.brand_id.shortcut or ""
            seq = rec.product_sequence or ""

            parts = [category_short, brand_short, seq]
            ref = "/".join([p for p in parts if p])

            if ref and rec.default_code != ref:
                rec.default_code = ref