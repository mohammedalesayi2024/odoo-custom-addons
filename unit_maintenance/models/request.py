import uuid
from urllib.parse import quote

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .utils import group_users, normalize_phone

REQUEST_TYPES = [('internal', 'داخلي'), ('external', 'خارجي')]
STATES = [
    ('new', 'جديد'),
    ('assigned', 'مسند لفني'),
    ('awaiting_price', 'بانتظار التسعير'),
    ('in_progress', 'قيد الصيانة'),
    ('done', 'مكتمل'),
    ('cancel', 'ملغي'),
]
EDITABLE_STATES = ('new', 'assigned', 'awaiting_price')
MANAGER = 'unit_maintenance.group_unit_maintenance_manager'


class UnitMaintenanceRequest(models.Model):
    _name = 'unit.maintenance.request'
    _description = 'طلب صيانة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('رقم الطلب', default='جديد', readonly=True, copy=False, index=True)
    request_type = fields.Selection(REQUEST_TYPES, 'نوع الصيانة', required=True, default='internal', tracking=True)
    state = fields.Selection(STATES, 'الحالة', default='new', tracking=True, copy=False, index=True)
    source = fields.Selection(
        [('phone', 'اتصال هاتفي'), ('app', 'شكوى من التطبيق'), ('internal', 'إنشاء داخلي')],
        'مصدر الطلب', default='phone')
    complaint_id = fields.Many2one('unit.maintenance.complaint', 'الشكوى', copy=False, readonly=True)

    unit_id = fields.Many2one('unit.maintenance.unit', 'الوحدة', required=True, index=True, tracking=True)
    building_id = fields.Many2one(related='unit_id.building_id', string='المبنى', store=True, index=True)
    owner_id = fields.Many2one(related='unit_id.owner_id', string='المالك', store=True, index=True)
    warranty_state = fields.Selection(related='unit_id.warranty_state', string='حالة الضمان')
    delivery_date = fields.Date(related='unit_id.delivery_date', string='تاريخ التسليم')
    warranty_months = fields.Integer(related='unit_id.warranty_months', string='مدة الضمان (بالأشهر)')
    warranty_end = fields.Date(related='unit_id.warranty_end', string='نهاية الضمان')
    cost_bearer = fields.Selection(
        [('adyar', 'شركة أديار'), ('customer', 'العميل')], string='الجهة المتحملة للتكلفة',
        compute='_compute_cost_bearer', store=True)
    contact_phone = fields.Char('رقم التواصل', compute='_compute_contact_phone', store=True, readonly=False)

    description = fields.Text('وصف المشكلة')
    request_date = fields.Datetime('تاريخ ووقت الطلب', default=fields.Datetime.now, required=True)
    visit_date = fields.Datetime('الموعد المقترح لزيارة العميل')
    technician_id = fields.Many2one('res.users', 'الفني', tracking=True, domain=[('share', '=', False)])

    line_ids = fields.One2many('unit.maintenance.request.line', 'request_id', 'المنتجات', copy=False)
    company_id = fields.Many2one('res.company', 'الشركة', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    amount_untaxed = fields.Monetary('الإجمالي قبل الضريبة', compute='_compute_totals', store=True)
    amount_tax = fields.Monetary('الضريبة', compute='_compute_totals', store=True)
    amount_total = fields.Monetary('الإجمالي بعد الضريبة', compute='_compute_totals', store=True)

    price_approved = fields.Boolean('تم اعتماد السعر', copy=False, tracking=True)
    price_approved_by = fields.Many2one('res.users', 'اعتمده', copy=False, readonly=True)
    price_approved_date = fields.Datetime('تاريخ الاعتماد', copy=False, readonly=True)
    signature = fields.Image('توقيع العميل', copy=False, attachment=True, max_width=800, max_height=400)
    signed_date = fields.Datetime('تاريخ التوقيع', copy=False, readonly=True)

    start_datetime = fields.Datetime('بداية الصيانة', copy=False, readonly=True)
    end_datetime = fields.Datetime('نهاية الصيانة', copy=False, readonly=True)
    duration = fields.Float('المدة (ساعات)', compute='_compute_duration', store=True)
    duration_text = fields.Char('المدة', compute='_compute_duration')
    report_text = fields.Text('تقرير الفني', copy=False)
    photo_ids = fields.One2many('unit.maintenance.photo', 'request_id', 'الصور', copy=False)
    photo_before_ids = fields.One2many(
        'unit.maintenance.photo', 'request_id', string='صور قبل الصيانة',
        domain=[('kind', '=', 'before')], copy=False)
    photo_after_ids = fields.One2many(
        'unit.maintenance.photo', 'request_id', string='صور بعد الصيانة',
        domain=[('kind', '=', 'after')], copy=False)

    report_sent = fields.Boolean('تم إرسال التقرير', copy=False, readonly=True)
    report_sent_date = fields.Datetime('آخر إرسال للتقرير', copy=False, readonly=True)
    send_log_ids = fields.One2many('unit.maintenance.send.log', 'request_id', 'سجل الإرسال')
    access_token = fields.Char(copy=False, readonly=True)
    invoice_id = fields.Many2one('account.move', 'الفاتورة', copy=False, readonly=True)

    # ------------------------------------------------------------------ helpers
    @api.depends('request_type')
    def _compute_cost_bearer(self):
        for rec in self:
            rec.cost_bearer = 'adyar' if rec.request_type == 'internal' else 'customer'

    @api.depends('owner_id.phone')
    def _compute_contact_phone(self):
        for rec in self:
            phone = rec.owner_id.phone
            if not phone and 'mobile' in rec.owner_id._fields:
                phone = rec.owner_id['mobile']
            rec.contact_phone = phone or False

    @api.depends('line_ids.subtotal', 'line_ids.tax_amount', 'line_ids.total')
    def _compute_totals(self):
        for rec in self:
            rec.amount_untaxed = sum(rec.line_ids.mapped('subtotal'))
            rec.amount_tax = sum(rec.line_ids.mapped('tax_amount'))
            rec.amount_total = sum(rec.line_ids.mapped('total'))

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            seconds = 0
            if rec.start_datetime and rec.end_datetime:
                seconds = max(int((rec.end_datetime - rec.start_datetime).total_seconds()), 0)
            rec.duration = seconds / 3600.0
            rec.duration_text = '%02d:%02d:%02d' % (seconds // 3600, seconds % 3600 // 60, seconds % 60)

    @api.model
    def _guess_type(self, unit_id, request_date=None):
        """نوع الطلب الافتراضي يؤخذ من نوع الصيانة المحدد على الوحدة."""
        unit = self.env['unit.maintenance.unit'].browse(unit_id)
        return unit.maintenance_type or 'internal'

    @api.onchange('unit_id', 'request_date')
    def _onchange_unit_set_type(self):
        if self.unit_id:
            self.request_type = self._guess_type(self.unit_id.id, self.request_date)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('request_type') and vals.get('unit_id'):
                vals['request_type'] = self._guess_type(vals['unit_id'], vals.get('request_date'))
            if not vals.get('name') or vals['name'] == 'جديد':
                code = 'unit.maintenance.request.%s' % ('ext' if vals.get('request_type') == 'external' else 'int')
                vals['name'] = self.env['ir.sequence'].next_by_code(code) or 'جديد'
            vals.setdefault('access_token', uuid.uuid4().hex)
        return super().create(vals_list)

    @property
    def _is_external(self):
        return self.request_type == 'external'

    def _has_lines(self):
        return bool(self.line_ids)

    def _is_priced(self):
        return self._has_lines() and self.price_approved

    def _reset_approval(self):
        for rec in self.filtered(lambda r: r.state in EDITABLE_STATES and (r.price_approved or r.signature)):
            rec.write({'price_approved': False, 'signature': False, 'signed_date': False,
                       'price_approved_by': False, 'price_approved_date': False})

    def _check_state(self, *states):
        for rec in self:
            if rec.state not in states:
                raise UserError(_('الإجراء غير متاح في الحالة الحالية للطلب %s.') % rec.name)

    # ------------------------------------------------------------------ workflow
    def action_assign(self):
        for rec in self:
            rec._check_state('new', 'assigned')
            if not rec.technician_id:
                raise UserError(_('اختر الفني أولاً.'))
            rec.state = 'assigned'
            rec.message_post(body=_('تم إسناد الطلب إلى %s.') % rec.technician_id.name)
            rec.message_subscribe(partner_ids=rec.technician_id.partner_id.ids)

    def action_request_price(self):
        """بعد إضافة المنتجات، ينتقل طلب الصيانة إلى الإدارة لاعتماد الأسعار في النوعين."""
        for rec in self:
            rec._check_state('assigned', 'awaiting_price')
            if not rec._has_lines():
                raise UserError(_('أضف منتجاً واحداً على الأقل.'))
            if not rec.price_approved:
                rec.state = 'awaiting_price'
                managers = group_users(self.env, MANAGER).partner_id
                rec.message_post(body=_('بانتظار تسعير واعتماد الإدارة.'), partner_ids=managers.ids,
                                 subtype_xmlid='mail.mt_comment')

    def action_fill_list_prices(self):
        for rec in self:
            rec._check_state('assigned', 'awaiting_price')
            for line in rec.line_ids.filtered(lambda l: not l.price_unit):
                line.price_unit = line.product_id.lst_price

    def action_approve_price(self):
        if not self.env.user.has_group(MANAGER):
            raise AccessError(_('اعتماد السعر من صلاحية مدير الصيانة.'))
        for rec in self:
            rec._check_state('awaiting_price', 'assigned')
            if not rec._has_lines():
                raise UserError(_('لا توجد منتجات في الطلب %s.') % rec.name)
            if any(l.price_unit < 0 for l in rec.line_ids):
                raise UserError(_('لا يمكن أن يكون سعر المنتج أقل من صفر.'))
            rec.write({'price_approved': True, 'price_approved_by': self.env.uid,
                       'price_approved_date': fields.Datetime.now(), 'state': 'assigned'})
            rec.message_post(body=_('تم اعتماد السعر. الإجمالي: %s') % rec.amount_total)

    def action_set_signature(self, image_b64):
        self.ensure_one()
        self._check_state('assigned')
        if not self._is_priced():
            raise UserError(_('يجب اعتماد السعر وإضافة المنتجات قبل توقيع العميل.'))
        self.write({'signature': image_b64, 'signed_date': fields.Datetime.now()})

    def action_start(self):
        for rec in self:
            rec._check_state('assigned')
            if not (rec._has_lines() and rec._is_priced() and rec.signature):
                raise UserError(_('أضف المنتجات، واعتمد الأسعار، واحصل على توقيع العميل قبل البدء.'))
            rec.write({'state': 'in_progress', 'start_datetime': fields.Datetime.now()})

    def action_finish(self, report_text):
        self.ensure_one()
        self._check_state('in_progress')
        if not (report_text or '').strip():
            raise UserError(_('اكتب تقرير الفني قبل إنهاء الصيانة.'))
        self.write({'state': 'done', 'end_datetime': fields.Datetime.now(), 'report_text': report_text.strip()})

    def action_cancel(self):
        for rec in self:
            rec._check_state('new', 'assigned', 'awaiting_price')
            rec.state = 'cancel'

    def action_reset(self):
        if not self.env.user.has_group(MANAGER):
            raise AccessError(_('إعادة الفتح من صلاحية مدير الصيانة.'))
        self.filtered(lambda r: r.state == 'cancel').write({'state': 'new'})

    # ------------------------------------------------------------------ report
    def _report_public_url(self):
        self.ensure_one()
        return '%s/unit_maintenance/report/%s/%s' % (self.get_base_url(), self.id, self.access_token)

    def _send_report(self, method='mail'):
        """يرسل (أو يعيد إرسال) التقرير. mail: بريد مع PDF، wa: رابط واتساب جاهز."""
        self.ensure_one()
        self._check_state('done')
        resend = self.report_sent
        result = {'method': method, 'resend': resend}
        recipient = self.owner_id.email or ''
        if method == 'mail':
            if not self.owner_id.email:
                raise UserError(_('لا يوجد بريد إلكتروني للمالك.'))
            pdf, _fmt = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'unit_maintenance.action_report_unit_request', self.ids)
            attachment = self.env['ir.attachment'].create({
                'name': '%s.pdf' % self.name, 'raw': pdf, 'mimetype': 'application/pdf',
                'res_model': self._name, 'res_id': self.id})
            self.message_post(
                subject=_('تقرير الصيانة %s') % self.name,
                body=_('نرفق لكم تقرير الصيانة رقم %s للوحدة %s.') % (self.name, self.unit_id.display_name),
                partner_ids=self.owner_id.ids, attachment_ids=attachment.ids,
                message_type='comment', subtype_xmlid='mail.mt_comment')
        elif method == 'wa':
            key = normalize_phone(self.contact_phone)
            if not key:
                raise UserError(_('لا يوجد رقم جوال للعميل.'))
            country = self.env['ir.config_parameter'].sudo().get_param('unit_maintenance.default_country_code', '966')
            text = _('تقرير الصيانة %s: %s') % (self.name, self._report_public_url())
            result['url'] = 'https://wa.me/%s%s?text=%s' % (country, key, quote(text))
            recipient = '+%s%s' % (country, key)
        else:
            raise UserError(_('طريقة الإرسال غير معروفة.'))
        self.env['unit.maintenance.send.log'].create({
            'request_id': self.id, 'method': method, 'recipient': recipient, 'is_resend': resend})
        self.write({'report_sent': True, 'report_sent_date': fields.Datetime.now()})
        return result

    def action_send_report(self):
        self.ensure_one()
        self._send_report('mail')
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': _('تم إرسال التقرير'), 'message': _('أُرسل التقرير بالبريد إلى %s.') % self.owner_id.email,
            'type': 'success', 'sticky': False}}

    def action_create_invoice(self):
        self.ensure_one()
        if not self._is_external or self.state != 'done':
            raise UserError(_('الفاتورة للطلبات الخارجية المكتملة فقط؛ الطلب الداخلي تتحمل تكلفته شركة أديار.'))
        if self.invoice_id:
            raise UserError(_('تم إنشاء فاتورة لهذا الطلب مسبقاً.'))
        move = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.owner_id.id, 'ref': self.name,
            'invoice_origin': self.name,
            'invoice_line_ids': [Command.create({
                'product_id': l.product_id.id, 'name': l.name, 'quantity': l.quantity,
                'price_unit': l.price_unit, 'tax_ids': [Command.set(l.tax_ids.ids)],
            }) for l in self.line_ids],
        })
        self.invoice_id = move
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': move.id,
                'view_mode': 'form'}
