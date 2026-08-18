from odoo import models, fields, api


class AuditTrackedModel(models.Model):
    _name = 'audit.tracked.model'
    _description = 'الموديلات الخاضعة للتدقيق'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        'ir.model', string='الموديل', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', string='الاسم التقني', store=True)
    active = fields.Boolean(string='مفعّل', default=True)
    track_create = fields.Boolean(string='تتبع الإضافة', default=True)
    track_write = fields.Boolean(string='تتبع التعديل', default=True)
    track_unlink = fields.Boolean(string='تتبع الحذف', default=True)

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)', 'هذا الموديل مضاف مسبقًا في قائمة التتبع.'),
    ]

    @api.model
    def _get_tracked_models_map(self):
        """يرجع dict مخزّن مؤقتًا بالموديلات المفعّلة ونوع العمليات المتتبعة لكل منها.
        مثال: {'sale.order': {'create': True, 'write': True, 'unlink': False}}
        """
        records = self.sudo().search([('active', '=', True)])
        return {
            rec.model_name: {
                'create': rec.track_create,
                'write': rec.track_write,
                'unlink': rec.track_unlink,
            }
            for rec in records if rec.model_name
        }
