from odoo import models, fields


class AdvanceAuditPolicy(models.Model):
    _name = 'advance.audit.policy'
    _description = 'Advance Audit Policy'

    name = fields.Char(
        string='Name',
        required=True
    )

    active = fields.Boolean(
        default=True
    )

    model_id = fields.Many2one(
    'ir.model',
    string='Model',
    required=True,
    ondelete='cascade'
   )

    track_create = fields.Boolean(
        string='Track Create',
        default=True
    )

    track_write = fields.Boolean(
        string='Track Update',
        default=True
    )

    track_delete = fields.Boolean(
        string='Track Delete',
        default=True
    )

    track_view = fields.Boolean(
        string='Track View'
    )

    track_search = fields.Boolean(
        string='Track Search'
    )