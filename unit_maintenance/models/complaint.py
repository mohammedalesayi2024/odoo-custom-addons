from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .utils import group_users


class UnitMaintenanceComplaint(models.Model):
    _name = 'unit.maintenance.complaint'
    _description = 'شكوى عميل'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char('رقم الشكوى', default='جديد', readonly=True, copy=False, index=True)
    state = fields.Selection([('new', 'جديدة'), ('converted', 'حُوّلت لطلب'), ('rejected', 'مرفوضة')],
                             'الحالة', default='new', tracking=True)
    phone = fields.Char('رقم الجوال', required=True)
    phone_key = fields.Char(index=True)
    unit_id = fields.Many2one('unit.maintenance.unit', 'الوحدة', required=True, tracking=True)
    building_id = fields.Many2one(related='unit_id.building_id', string='المبنى', store=True)
    owner_id = fields.Many2one(related='unit_id.owner_id', string='المالك', store=True)
    description = fields.Text('المشكلة', required=True)
    ip_address = fields.Char('عنوان IP', readonly=True)
    request_id = fields.Many2one('unit.maintenance.request', 'طلب الصيانة', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'جديد':
                vals['name'] = self.env['ir.sequence'].next_by_code('unit.maintenance.complaint') or 'جديد'
        records = super().create(vals_list)
        managers = group_users(self.env, 'unit_maintenance.group_unit_maintenance_user').partner_id
        for rec in records:
            rec.message_post(
                body=_('شكوى جديدة من %s بخصوص %s.') % (rec.owner_id.name, rec.unit_id.display_name),
                partner_ids=managers.ids, subtype_xmlid='mail.mt_comment')
        return records

    def action_convert(self):
        self.ensure_one()
        if self.state != 'new':
            raise UserError(_('الشكوى ليست جديدة.'))
        request = self.env['unit.maintenance.request'].create({
            'unit_id': self.unit_id.id, 'description': self.description, 'source': 'app',
            'complaint_id': self.id, 'contact_phone': self.phone,
        })
        self.write({'state': 'converted', 'request_id': request.id})
        return {'type': 'ir.actions.act_window', 'res_model': 'unit.maintenance.request',
                'res_id': request.id, 'view_mode': 'form'}

    def action_reject(self):
        self.filtered(lambda c: c.state == 'new').write({'state': 'rejected'})

    def action_open_request(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'unit.maintenance.request',
                'res_id': self.request_id.id, 'view_mode': 'form'}
