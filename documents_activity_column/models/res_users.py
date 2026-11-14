from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    activity_can_complete_others = fields.Boolean(
        string='Complete Other Users’ Activities',
        help='Allow this user to mark activities assigned to other users as done.',
    )
    activity_can_cancel_others = fields.Boolean(
        string='Cancel Other Users’ Activities',
        help='Allow this user to cancel/delete activities created by or assigned to other users.',
    )
    activity_can_reschedule_others = fields.Boolean(
        string='Reschedule Other Users’ Activities',
        help='Allow this user to change the deadline or assignee of other users’ activities.',
    )
    activity_can_edit_others = fields.Boolean(
        string='Edit Other Users’ Activities',
        help='Allow this user to edit other users’ activities.',
    )
    activity_can_delete_others = fields.Boolean(
        string='Delete Other Users’ Activities',
        help='Allow this user to permanently delete other users’ activities.',
    )

    def _has_activity_supervisor_permission(self, permission):
        self.ensure_one()
        return bool(self[permission])
