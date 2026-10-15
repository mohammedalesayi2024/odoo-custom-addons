from odoo import fields, models, _
from odoo.exceptions import AccessError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    activity_status = fields.Selection(
        selection=[
            ("open", "Open"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Activity Status",
        default="open",
        required=True,
        index=True,
        copy=False,
        help="Persistent status; cancelled activities are archived instead of deleted.",
    )

    def _is_creator_or_admin(self):
        user = self.env.user
        return user._is_admin() or all(activity.create_uid.id == user.id for activity in self)

    def _check_can_complete_activity(self):
        user = self.env.user
        if user._is_admin():
            return
        for activity in self:
            if activity.create_uid.id == user.id or activity.user_id.id == user.id:
                continue
            raise AccessError(_(
                "You can only mark activities assigned to you as done. "
                "Only the creator or a system administrator can complete an "
                "activity assigned to another user."
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
            allowed_fields = {"active", "feedback", "activity_status"}
            if set(vals) - allowed_fields and not self._is_creator_or_admin():
                raise AccessError(_("You cannot edit this activity while completing it."))
        elif not self._is_creator_or_admin():
            raise AccessError(_(
                "Only the creator or a system administrator can edit or reassign "
                "this activity. You may complete an activity assigned to you."
            ))
        return super().write(vals)

    def unlink(self):
        """The standard Activities Cancel button may call unlink directly.
        Convert that operation into a soft cancellation to preserve history.
        """
        if self.env.context.get("activity_creator_permissions_force_delete"):
            if not self._is_creator_or_admin():
                raise AccessError(_("Only the creator or a system administrator can delete activities."))
            return super().unlink()

        if not self._is_creator_or_admin():
            raise AccessError(_(
                "Only the creator or a system administrator can cancel this activity."
            ))

        activities = self.filtered(lambda activity: activity.activity_status != "cancelled")
        if activities:
            activities.with_context(
                activity_creator_permissions_completion=True
            ).write({
                "active": False,
                "activity_status": "cancelled",
            })
        return True

    def action_cancel(self):
        if not self._is_creator_or_admin():
            raise AccessError(_("Only the creator or a system administrator can cancel it."))
        activities = self.filtered(lambda activity: activity.activity_status != "cancelled")
        if activities:
            activities.with_context(
                activity_creator_permissions_completion=True
            ).write({"active": False, "activity_status": "cancelled"})
        return True

    def action_done(self):
        self._check_can_complete_activity()
        result = super().action_done()
        completed = self.filtered(lambda activity: not activity.active)
        if completed:
            completed.with_context(
                activity_creator_permissions_completion=True
            ).write({"activity_status": "done"})
        return result

    def action_feedback(self, feedback=False, attachment_ids=None):
        self._check_can_complete_activity()
        result = super(
            MailActivity,
            self.with_context(activity_creator_permissions_completion=True)
        ).action_feedback(feedback=feedback, attachment_ids=attachment_ids)
        completed = self.filtered(lambda activity: not activity.active)
        if completed:
            completed.with_context(
                activity_creator_permissions_completion=True
            ).write({"activity_status": "done"})
        return result

    def action_feedback_schedule_next(self, feedback=False, attachment_ids=None):
        self._check_can_complete_activity()
        result = super(
            MailActivity,
            self.with_context(activity_creator_permissions_completion=True)
        ).action_feedback_schedule_next(feedback=feedback, attachment_ids=attachment_ids)
        completed = self.filtered(lambda activity: not activity.active)
        if completed:
            completed.with_context(
                activity_creator_permissions_completion=True
            ).write({"activity_status": "done"})
        return result
