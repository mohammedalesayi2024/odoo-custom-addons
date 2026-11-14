from odoo import _, models
from odoo.exceptions import AccessError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def _is_activity_creator(self):
        self.ensure_one()
        return self.create_uid == self.env.user

    def _is_activity_assignee(self):
        self.ensure_one()
        return self.user_id == self.env.user

    def _check_activity_permission(self, supervisor_field, allow_assignee=False):
        """Check the explicit business permission before using sudo internally.

        Odoo's standard mail.activity methods independently restrict completing
        or changing another user's activity. Once this module has authorized
        the operation, the parent implementation is called in sudo mode so
        that the standard check/record rule does not reject the authorized
        supervisor a second time.
        """
        user = self.env.user
        for activity in self:
            if activity._is_activity_creator():
                continue
            if allow_assignee and activity._is_activity_assignee():
                continue
            if supervisor_field and user[supervisor_field]:
                continue
            raise AccessError(
                _('You are not allowed to perform this operation on this activity.')
            )

    def write(self, vals):
        if self.env.su or self.env.context.get('activity_permission_bypass'):
            return super().write(vals)

        protected = set(vals) - {'message_ids', 'attachment_ids'}
        if not protected:
            return super().write(vals)

        # A pure deadline/assignee change is rescheduling. Any other business
        # field change requires the separate edit permission.
        schedule_fields = {'date_deadline', 'user_id'}
        if protected <= schedule_fields:
            self._check_activity_permission('activity_can_reschedule_others')
        else:
            self._check_activity_permission('activity_can_edit_others')

        # The explicit check above is the authorization boundary. Sudo is
        # needed here because Odoo's native activity ACL/rules do not know
        # about this module's per-user delegated permissions.
        return super(MailActivity, self.sudo()).write(vals)

    def action_feedback(self, feedback=False, attachment_ids=None):
        if not self.env.su:
            self._check_activity_permission(
                'activity_can_complete_others', allow_assignee=True
            )
        # Odoo's own action_feedback checks creator/assignee/admin and would
        # reject an authorized supervisor. Run the parent operation in sudo
        # only after our per-user permission check has succeeded.
        return super(MailActivity, self.sudo().with_context(
            activity_permission_bypass=True
        )).action_feedback(feedback=feedback, attachment_ids=attachment_ids)

    def action_feedback_schedule_next(self, feedback=False):
        if not self.env.su:
            self._check_activity_permission(
                'activity_can_complete_others', allow_assignee=True
            )
        return super(MailActivity, self.sudo().with_context(
            activity_permission_bypass=True
        )).action_feedback_schedule_next(feedback=feedback)

    def action_done(self):
        if not self.env.su:
            self._check_activity_permission(
                'activity_can_complete_others', allow_assignee=True
            )
        return super(MailActivity, self.sudo().with_context(
            activity_permission_bypass=True
        )).action_done()

    def action_unlink(self):
        if not self.env.su:
            self._check_activity_permission('activity_can_cancel_others')
        return super(MailActivity, self.sudo().with_context(
            activity_permission_bypass=True
        )).action_unlink()

    def unlink(self):
        if self.env.su or self.env.context.get('activity_permission_bypass'):
            return super().unlink()
        self._check_activity_permission('activity_can_delete_others')
        return super(MailActivity, self.sudo()).unlink()
