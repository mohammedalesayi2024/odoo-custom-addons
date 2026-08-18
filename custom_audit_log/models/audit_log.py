from odoo import models, fields, api


class AuditLog(models.Model):
    _name = 'audit.log'
    _description = 'سجل تدقيق العمليات'
    _order = 'log_date desc, id desc'
    _rec_name = 'record_name'

    user_id = fields.Many2one(
        'res.users', string='المستخدم', required=True, index=True, readonly=True)
    model_name = fields.Char(string='الموديل التقني', required=True, index=True, readonly=True)
    model_label = fields.Char(string='اسم الموديل', readonly=True)
    res_id = fields.Integer(string='معرف السجل', required=True, readonly=True)
    record_name = fields.Char(string='اسم السجل', readonly=True)
    method = fields.Selection([
        ('create', 'إضافة'),
        ('write', 'تعديل'),
        ('unlink', 'حذف'),
    ], string='نوع العملية', required=True, index=True, readonly=True)
    log_date = fields.Datetime(
        string='تاريخ ووقت العملية', default=fields.Datetime.now, index=True, readonly=True)
    field_changes_ids = fields.One2many(
        'audit.log.line', 'audit_log_id', string='تفاصيل التغييرات', readonly=True)
    changes_summary = fields.Text(
        string='ملخص التغييرات', compute='_compute_changes_summary', store=False)

    @api.depends('field_changes_ids')
    def _compute_changes_summary(self):
        for rec in self:
            lines = []
            for line in rec.field_changes_ids:
                lines.append(f"{line.field_label}: '{line.old_value}' → '{line.new_value}'")
            rec.changes_summary = '\n'.join(lines) if lines else ''

    def name_get(self):
        result = []
        for rec in self:
            label = f"[{rec.method}] {rec.model_label or rec.model_name} - {rec.record_name or rec.res_id}"
            result.append((rec.id, label))
        return result


class AuditLogLine(models.Model):
    _name = 'audit.log.line'
    _description = 'تفاصيل الحقل المعدل في سجل التدقيق'

    audit_log_id = fields.Many2one(
        'audit.log', string='سجل التدقيق', ondelete='cascade', required=True, index=True)
    field_name = fields.Char(string='اسم الحقل التقني')
    field_label = fields.Char(string='تسمية الحقل')
    old_value = fields.Text(string='القيمة قبل التعديل')
    new_value = fields.Text(string='القيمة بعد التعديل')
