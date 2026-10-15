from odoo import api, models, _
from odoo.exceptions import AccessError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _activity_is_creator_or_admin(self):
        """Only the activity creator and system administrators manage it."""
        user = self.env.user
        return user._is_admin() or all(activity.create_uid.id == user.id for activity in self)

    def _compute_can_write(self):
        """Hide edit/cancel controls for users other than the creator/admin."""
        super()._compute_can_write()
        user = self.env.user
        if user._is_admin():
            return
        for activity in self:
            if activity.create_uid.id != user.id:
                activity.can_write = False

    def write(self, vals):
        # The assignee may complete an activity through Odoo's standard
        # action_feedback flow. Other direct changes are reserved for creator/admin.
        if not self.env.context.get("activity_creator_permissions_completion"):
            if not self._activity_is_creator_or_admin():
                raise AccessError(_(
                    "Only the user who created this activity or a system administrator "
                    "can edit or reassign it. You may still mark an activity assigned "
                    "to you as done using the standard completion action."
                ))
        else:
            # During completion, allow only the archive/feedback fields used by Odoo.
            allowed_fields = {"active", "feedback"}
            if set(vals) - allowed_fields:
                if not self._activity_is_creator_or_admin():
                    raise AccessError(_("You cannot edit this activity while completing it."))
        return super().write(vals)

    def unlink(self):
        if not self._activity_is_creator_or_admin():
            raise AccessError(_(
                "Only the user who created this activity or a system administrator "
                "can cancel or delete it."
            ))
        return super().unlink()

    def action_feedback(self, feedback=False, attachment_ids=None):
        # Odoo completes an activity by archiving it. Pass a private context flag
        # so the completion write is allowed without granting general edit rights.
        return super(
            MailActivity,
            self.with_context(activity_creator_permissions_completion=True)
        ).action_feedback(feedback=feedback, attachment_ids=attachment_ids)

    def action_feedback_schedule_next(self, feedback=False, attachment_ids=None):
        return super(
            MailActivity,
            self.with_context(activity_creator_permissions_completion=True)
        ).action_feedback_schedule_next(feedback=feedback, attachment_ids=attachment_ids)
