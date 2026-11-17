from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .request import EDITABLE_STATES

PRICE_FIELDS = {'product_id', 'quantity', 'price_unit', 'tax_ids'}


def _customer_taxes(product, company):
    fname = 'taxes_id' if 'taxes_id' in product._fields else 'tax_ids'
    return product[fname].filtered(lambda t: t.company_id == company)


class UnitMaintenanceRequestLine(models.Model):
    _name = 'unit.maintenance.request.line'
    _description = 'منتج في طلب صيانة'
    _order = 'sequence, id'

    request_id = fields.Many2one('unit.maintenance.request', 'الطلب', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', 'المنتج', required=True, domain=[('sale_ok', '=', True)])
    name = fields.Char('الوصف', compute='_compute_name', store=True, readonly=False)
    quantity = fields.Float('الكمية', default=1.0, required=True)
    price_unit = fields.Float('السعر', digits='Product Price',
                              help='تحدده الإدارة. في الصيانة الداخلية لا يُحتسب.')
    tax_ids = fields.Many2many('account.tax', 'unit_maintenance_line_tax_rel', 'line_id', 'tax_id', 'الضرائب',
                               compute='_compute_tax_ids', store=True, readonly=False,
                               domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(related='request_id.currency_id')
    subtotal = fields.Monetary('قبل الضريبة', compute='_compute_amounts', store=True)
    tax_amount = fields.Monetary('الضريبة', compute='_compute_amounts', store=True)
    total = fields.Monetary('الإجمالي', compute='_compute_amounts', store=True)

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            line.name = line.product_id.display_name or ''

    @api.depends('product_id', 'request_id.company_id')
    def _compute_tax_ids(self):
        for line in self:
            line.tax_ids = _customer_taxes(line.product_id, line.request_id.company_id)

    @api.depends('quantity', 'price_unit', 'tax_ids', 'request_id.request_type', 'currency_id')
    def _compute_amounts(self):
        for line in self:
            if line.request_id.request_type == 'internal':
                line.subtotal = line.tax_amount = line.total = 0.0
                continue
            res = line.tax_ids.compute_all(
                line.price_unit, currency=line.currency_id, quantity=line.quantity,
                product=line.product_id, partner=line.request_id.owner_id)
            line.subtotal = res['total_excluded']
            line.total = res['total_included']
            line.tax_amount = res['total_included'] - res['total_excluded']

    def _check_request_editable(self):
        for request in self.request_id:
            if request.state not in EDITABLE_STATES:
                raise UserError(_('لا يمكن تعديل المنتجات بعد بدء الصيانة (الطلب %s).') % request.name)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._check_request_editable()
        lines.request_id._reset_approval()
        return lines

    def write(self, vals):
        self._check_request_editable()
        res = super().write(vals)
        if PRICE_FIELDS & set(vals):
            self.request_id._reset_approval()
        return res

    def unlink(self):
        self._check_request_editable()
        requests = self.request_id
        res = super().unlink()
        requests._reset_approval()
        return res


class UnitMaintenancePhoto(models.Model):
    _name = 'unit.maintenance.photo'
    _description = 'صورة صيانة'
    _order = 'kind, id'

    request_id = fields.Many2one('unit.maintenance.request', 'الطلب', required=True, ondelete='cascade', index=True)
    kind = fields.Selection([('before', 'قبل الصيانة'), ('after', 'بعد الصيانة')], 'النوع', required=True)
    image = fields.Image('الصورة', required=True, attachment=True, max_width=1600, max_height=1600)
    note = fields.Char('ملاحظة')


class UnitMaintenanceSendLog(models.Model):
    _name = 'unit.maintenance.send.log'
    _description = 'سجل إرسال تقرير الصيانة'
    _order = 'id desc'

    request_id = fields.Many2one('unit.maintenance.request', 'الطلب', required=True, ondelete='cascade', index=True)
    method = fields.Selection([('mail', 'بريد إلكتروني'), ('wa', 'واتساب')], 'الطريقة', required=True)
    recipient = fields.Char('المستلم')
    is_resend = fields.Boolean('إعادة إرسال')
    user_id = fields.Many2one('res.users', 'بواسطة', default=lambda self: self.env.user)
    date = fields.Datetime('التاريخ', default=fields.Datetime.now)
