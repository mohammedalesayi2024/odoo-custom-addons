from odoo import api, fields, models


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    open_activity_summary = fields.Text(
        string="Activity",
        compute="_compute_open_activity_summary",
        help="Open activities, assigned users, and deadlines for this document.",
    )

    @api.depends("name")
    def _compute_open_activity_summary(self):
        # Compute in batches to avoid one query per document.
        for document in self:
            document.open_activity_summary = ""

        documents = self.filtered(lambda doc: doc.id)
        if not documents:
            return

        activities = self.env["mail.activity"].search([
            ("res_model", "=", "documents.document"),
            ("res_id", "in", documents.ids),
        ], order="date_deadline, id")

        by_document = {}
        for activity in activities:
            parts = []
            activity_type = activity.activity_type_id.display_name
            if activity_type:
                parts.append(activity_type)

            if activity.summary:
                parts.append(activity.summary)

            if activity.user_id:
                parts.append("Assigned to: %s" % activity.user_id.display_name)

            if activity.date_deadline:
                parts.append("Due: %s" % fields.Date.to_string(activity.date_deadline))

            line = " — ".join(parts) if parts else "Open activity"
            by_document.setdefault(activity.res_id, []).append(line)

        for document in documents:
            document.open_activity_summary = "\n".join(
                by_document.get(document.id, [])
            )
