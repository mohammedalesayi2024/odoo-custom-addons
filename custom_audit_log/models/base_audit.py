import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

# موديلات مستثناة دائمًا بغض النظر عن الإعدادات، لتفادي الحلقات اللانهائية
# وتسجيل ضجيج غير مفيد (سجلات النظام الداخلية).
ALWAYS_EXCLUDED = {
    'audit.log', 'audit.log.line', 'audit.tracked.model',
    'ir.logging', 'bus.bus', 'ir.cron', 'ir.cron.trigger',
    'mail.message', 'mail.tracking.value', 'mail.notification',
    'bus.presence',
}


class Base(models.AbstractModel):
    _inherit = 'base'

    def _audit_get_tracked_config(self):
        """يرجع إعدادات التتبع لهذا الموديل إن كان مفعّلًا، أو None إن لم يكن مفعّلًا."""
        if self._name in ALWAYS_EXCLUDED or self._name.startswith('ir.'):
            return None
        if self.env.context.get('skip_audit'):
            return None
        tracked_map = self.env['audit.tracked.model'].sudo()._get_tracked_models_map()
        return tracked_map.get(self._name)

    def _audit_field_label(self, field_name):
        field = self._fields.get(field_name)
        return field.string if field else field_name

    def _audit_format_value(self, field_name, value):
        """تحويل القيمة لنص قابل للقراءة، مع معالجة الحقول العلائقية."""
        field = self._fields.get(field_name)
        try:
            if field and field.type in ('many2one',):
                return value.display_name if value else ''
            if field and field.type in ('many2many', 'one2many'):
                return ', '.join(value.mapped('display_name')) if value else ''
            if value is False or value is None:
                return ''
            return str(value)
        except Exception:
            _logger.warning('audit: تعذر تنسيق قيمة الحقل %s', field_name, exc_info=True)
            return str(value)

    def write(self, vals):
        config = self._audit_get_tracked_config()
        if not config or not config.get('write') or not vals:
            return super().write(vals)

        # نلتقط القيم القديمة قبل تنفيذ التعديل
        old_data = {}
        for rec in self:
            old_data[rec.id] = {
                f: rec[f] for f in vals.keys() if f in rec._fields
            }

        result = super().write(vals)

        AuditLog = self.env['audit.log'].sudo()
        model_label = self.env['ir.model'].sudo()._get(self._name).name
        for rec in self:
            lines = []
            for field_name in vals.keys():
                if field_name not in rec._fields:
                    continue
                old_val_raw = old_data[rec.id].get(field_name)
                new_val_raw = rec[field_name]
                old_val = self._audit_format_value(field_name, old_val_raw)
                new_val = self._audit_format_value(field_name, new_val_raw)
                if old_val == new_val:
                    continue
                lines.append((0, 0, {
                    'field_name': field_name,
                    'field_label': rec._audit_field_label(field_name),
                    'old_value': old_val,
                    'new_value': new_val,
                }))
            if lines:
                AuditLog.create({
                    'user_id': self.env.uid,
                    'model_name': rec._name,
                    'model_label': model_label,
                    'res_id': rec.id,
                    'record_name': rec.display_name,
                    'method': 'write',
                    'field_changes_ids': lines,
                })
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        config = self._audit_get_tracked_config()
        if config and config.get('create'):
            AuditLog = self.env['audit.log'].sudo()
            model_label = self.env['ir.model'].sudo()._get(self._name).name
            for rec, vals in zip(records, vals_list):
                lines = []
                for field_name in vals.keys():
                    if field_name not in rec._fields:
                        continue
                    new_val = self._audit_format_value(field_name, rec[field_name])
                    lines.append((0, 0, {
                        'field_name': field_name,
                        'field_label': rec._audit_field_label(field_name),
                        'old_value': '',
                        'new_value': new_val,
                    }))
                AuditLog.create({
                    'user_id': self.env.uid,
                    'model_name': rec._name,
                    'model_label': model_label,
                    'res_id': rec.id,
                    'record_name': rec.display_name,
                    'method': 'create',
                    'field_changes_ids': lines,
                })
        return records

    def unlink(self):
        config = self._audit_get_tracked_config()
        if config and config.get('unlink'):
            AuditLog = self.env['audit.log'].sudo()
            model_label = self.env['ir.model'].sudo()._get(self._name).name
            log_vals = [{
                'user_id': self.env.uid,
                'model_name': rec._name,
                'model_label': model_label,
                'res_id': rec.id,
                'record_name': rec.display_name,
                'method': 'unlink',
            } for rec in self]
            result = super().unlink()
            AuditLog.create(log_vals)
            return result
        return super().unlink()
