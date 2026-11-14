from odoo import _, models
from odoo.exceptions import AccessError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    _ACTIVITY_PERMISSION_FIELDS = {
        'activity_can_complete_others',
        'activity_can_cancel_others',
        'activity_can_reschedule_others',
        'activity_can_edit_others',
        'activity_can_delete_others',
    }

    def _is_activity_creator(self):
        self.ensure_one()
        return self.create_uid == self.env.user

    def _is_activity_assignee(self):
        self.ensure_one()
        return self.user_id == self.env.user

    def _check_activity_permission(self, supervisor_field, allow_assignee=False):
        user = self.env.user
        for activity in self:
            if activity._is_activity_creator():
                continue
            if allow_assignee and activity._is_activity_assignee():
                continue
            if supervisor_field and user[supervisor_field]:
                continue
            raise AccessError(_('You are not allowed to perform this operation on this activity.'))

    def write(self, vals):
        if self.env.su or self.env.context.get('activity_permission_bypass'):
            return super().write(vals)

        protected = set(vals) - {'message_ids', 'attachment_ids'}
        if not protected:
            return super().write(vals)

        # Changing the deadline or assignee is a scheduling operation. Other
        # changes are treated as editing the activity.
        schedule_fields = {'date_deadline', 'user_id'}
        if protected <= schedule_fields:
            self._check_activity_permission('activity_can_reschedule_others')
        else:
            self._check_activity_permission('activity_can_edit_others')
        return super().write(vals)

    def action_feedback(self, feedback=False, attachment_ids=None):
        if not self.env.su:
            self._check_activity_permission(
                'activity_can_complete_others', allow_assignee=True
            )
        # Odoo completes an activity by posting its feedback and removing the
        # pending activity. Bypass only the internal unlink performed here.
        return super(MailActivity, self.with_context(
            activity_permission_bypass=True
        )).action_feedback(feedback=feedback, attachment_ids=attachment_ids)

    def action_feedback_schedule_next(self, feedback=False):
        if not self.env.su:
            self._check_activity_permission(
                'activity_can_complete_others', allow_assignee=True
            )
        return super(MailActivity, self.with_context(
            activity_permission_bypass=True
        )).action_feedback_schedule_next(feedback=feedback)

    def action_done(self):
        if not self.env.su:
            self._check_activity_permission(
                'activity_can_complete_others', allow_assignee=True
            )
        return super(MailActivity, self.with_context(
            activity_permission_bypass=True
        )).action_done()

    def action_unlink(self):
        if not self.env.su:
            for activity in self:
                if activity._is_activity_creator():
                    continue
                if self.env.user.activity_can_cancel_others:
                    continue
                raise AccessError(_('Only the activity creator or an authorized supervisor can cancel this activity.'))
        return super(MailActivity, self.with_context(
            activity_permission_bypass=True
        )).action_unlink()

    def unlink(self):
        if self.env.su or self.env.context.get('activity_permission_bypass'):
            return super().unlink()
        for activity in self:
            if activity._is_activity_creator():
                continue
            if self.env.user.activity_can_delete_others:
                continue
            raise AccessError(_('Only the activity creator or an authorized supervisor can cancel or delete this activity.'))
        return super().unlink()
