from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class UnitMaintenanceBuilding(models.Model):
    _name = 'unit.maintenance.building'
    _description = 'مبنى'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char('اسم المبنى', required=True, tracking=True)
    code = fields.Char('رقم المبنى')
    address = fields.Char('العنوان / المدينة')
    map_url = fields.Char('رابط الموقع على الخريطة')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', 'الشركة', default=lambda self: self.env.company)
    unit_ids = fields.One2many('unit.maintenance.unit', 'building_id', 'الوحدات')
    unit_count = fields.Integer('عدد الوحدات', compute='_compute_unit_count')

    @api.depends('unit_ids')
    def _compute_unit_count(self):
        for rec in self:
            rec.unit_count = len(rec.unit_ids)

    def action_view_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': _('الوحدات'),
            'res_model': 'unit.maintenance.unit', 'view_mode': 'list,form',
            'domain': [('building_id', '=', self.id)],
            'context': {'default_building_id': self.id},
        }


class UnitMaintenanceUnit(models.Model):
    _name = 'unit.maintenance.unit'
    _description = 'وحدة سكنية'
    _inherit = ['mail.thread']
    _order = 'building_id, number'
    _rec_names_search = ['number', 'building_id', 'owner_id']

    number = fields.Char('رقم الوحدة', required=True, tracking=True)
    building_id = fields.Many2one('unit.maintenance.building', 'المبنى', required=True, index=True, tracking=True)
    owner_id = fields.Many2one('res.partner', 'المالك', required=True, index=True, tracking=True)
    maintenance_type = fields.Selection(
        [('internal', 'داخلية (على شركة أديار)'), ('external', 'خارجية (على العميل)')],
        'نوع الصيانة', required=True, default='internal', tracking=True,
        help='يُستخدم النوع تلقائياً عند إنشاء طلب صيانة لهذه الوحدة.')
    delivery_date = fields.Date('تاريخ التسليم', tracking=True)
    warranty_months = fields.Integer('مدة الضمان (بالأشهر)', default=lambda self: self._default_warranty_months(), tracking=True)
    warranty_end = fields.Date('نهاية الضمان', compute='_compute_warranty_end', store=True)
    warranty_state = fields.Selection(
        [('under', 'تحت الضمان'), ('expired', 'انتهى الضمان'), ('unknown', 'غير محدد')],
        'حالة الضمان', compute='_compute_warranty_state')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', 'الشركة', default=lambda self: self.env.company)
    request_ids = fields.One2many('unit.maintenance.request', 'unit_id', 'طلبات الصيانة')
    request_count = fields.Integer('عدد الطلبات', compute='_compute_request_count')

    @api.model
    def _default_warranty_months(self):
        value = self.env['ir.config_parameter'].sudo().get_param('unit_maintenance.default_warranty_months', '24')
        return int(value) if str(value).isdigit() else 24

    @api.constrains('number', 'building_id')
    def _check_unique_number(self):
        for rec in self:
            if self.with_context(active_test=False).search_count(
                    [('id', '!=', rec.id), ('number', '=', rec.number), ('building_id', '=', rec.building_id.id)]):
                raise ValidationError(_('رقم الوحدة مكرر في نفس المبنى.'))

    @api.depends('delivery_date', 'warranty_months')
    def _compute_warranty_end(self):
        for rec in self:
            rec.warranty_end = (rec.delivery_date + relativedelta(months=rec.warranty_months)
                                if rec.delivery_date else False)

    @api.depends('warranty_end')
    def _compute_warranty_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.warranty_end:
                rec.warranty_state = 'unknown'
            else:
                rec.warranty_state = 'under' if rec.warranty_end >= today else 'expired'

    @api.depends('request_ids')
    def _compute_request_count(self):
        for rec in self:
            rec.request_count = len(rec.request_ids)

    @api.depends('number', 'building_id.name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s · %s' % (rec.building_id.name or '', rec.number or '')

    def action_view_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': _('طلبات الصيانة'),
            'res_model': 'unit.maintenance.request', 'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {'default_unit_id': self.id},
        }
