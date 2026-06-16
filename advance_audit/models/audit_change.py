from odoo import models, fields


class AdvanceAuditChange(models.Model):
    _name = 'advance.audit.change'
    _description = 'Advance Audit Change'

    event_id = fields.Many2one(
        'advance.audit.event',
        required=True,
        ondelete='cascade'
    )

    field_name = fields.Char(
        string='Field'
    )

    old_value = fields.Text(
        string='Old Value'
    )

    new_value = fields.Text(
        string='New Value'
    )