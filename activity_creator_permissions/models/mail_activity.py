from odoo import models, _
from odoo.exceptions import AccessError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _is_creator_or_admin(self):
        user = self.env.user
        return user._is_admin() or all(activity.create_uid.id == user.id for activity in self)

    def _check_can_complete_activity(self):
        """Assignees may complete only activities assigned to themselves."""
        user = self.env.user
        if user._is_admin():
            return
        for activity in self:
            if activity.create_uid.id == user.id:
                continue
            if activity.user_id.id != user.id:
                raise AccessError(_(
                    "You can only mark activities assigned to you as done. "
                    "Only the activity creator or a system administrator can "
                    "complete an activity assigned to another user."
                ))

    def _compute_can_write(self):
        super()._compute_can_write()
        user = self.env.user
        if user._is_admin():
            return
        for activity in self:
            if activity.create_uid.id != user.id:
                activity.can_write = False

    def write(self, vals):
        if self.env.context.get("activity_creator_permissions_completion"):
            allowed_fields = {"active", "feedback"}
            if set(vals) - allowed_fields and not self._is_creator_or_admin():
                raise AccessError(_("You cannot edit this activity while completing it."))
        elif not self._is_creator_or_admin():
            raise AccessError(_(
                "Only the user who created this activity or a system administrator "
                "can edit or reassign it. You may complete an activity assigned to you."
            ))
        return super().write(vals)

    def unlink(self):
        if not self._is_creator_or_admin():
            raise AccessError(_(
                "Only the user who created this activity or a system administrator "
                "can cancel or delete it."
            ))
        return super().unlink()

    def action_done(self):
        self._check_can_complete_activity()
        return super().action_done()

    def action_feedback(self, feedback=False, attachment_ids=None):
        self._check_can_complete_activity()
        return super(
            MailActivity,
            self.with_context(activity_creator_permissions_completion=True)
        ).action_feedback(feedback=feedback, attachment_ids=attachment_ids)

    def action_feedback_schedule_next(self, feedback=False, attachment_ids=None):
        self._check_can_complete_activity()
        return super(
            MailActivity,
            self.with_context(activity_creator_permissions_completion=True)
        ).action_feedback_schedule_next(feedback=feedback, attachment_ids=attachment_ids)
