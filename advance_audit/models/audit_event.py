from odoo import models, fields


class AdvanceAuditEvent(models.Model):
    _name = 'advance.audit.event'
    _description = 'Advance Audit Event'
    _order = 'event_datetime desc'

    name = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        index=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True,
        required=True,
        index=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        index=True,
    )

    event_type = fields.Selection([
        ('create', 'Create'),
        ('write', 'Write'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('cancel', 'Cancel'),
        ('draft', 'Reset To Draft'),
        ('view', 'View'),
        ('search', 'Search'),
    ],
        string='Operation',
        required=True,
        index=True,
    )

    model_name = fields.Char(
        string='Technical Model'
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        index=True,
    )

    record_id = fields.Integer(
        string='Record ID',
        index=True,
    )

    record_name = fields.Char(
        string='Record Name'
    )

    description = fields.Text(
        string='Description'
    )

    event_datetime = fields.Datetime(
        string='Date Time',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        index=True,
    )

    change_ids = fields.One2many(
        'advance.audit.change',
        'event_id',
        string='Changes',
    )