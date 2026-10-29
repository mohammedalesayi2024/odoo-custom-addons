from odoo import fields, models


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    open_activity_summary = fields.Text(
        string="Activity",
        compute="_compute_open_activity_summary",
    )

    def _compute_open_activity_summary(self):
        summaries = {doc.id: [] for doc in self}
        if self.ids:
            activities = self.env["mail.activity"].search([
                ("res_model", "=", "documents.document"),
                ("res_id", "in", self.ids),
            ], order="date_deadline, id")
            for activity in activities:
                parts = []
                if activity.activity_type_id:
                    parts.append(activity.activity_type_id.display_name)
                if activity.summary:
                    parts.append(activity.summary)
                if activity.user_id:
                    parts.append("Assigned to: %s" % activity.user_id.display_name)
                if activity.date_deadline:
                    parts.append("Due: %s" % fields.Date.to_string(activity.date_deadline))
                summaries[activity.res_id].append(" — ".join(parts) or "Open activity")
        for document in self:
            document.open_activity_summary = "\\n".join(summaries.get(document.id, []))
