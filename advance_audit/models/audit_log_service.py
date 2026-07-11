from odoo import models


class AdvanceAuditLogService(models.AbstractModel):
    _name = "advance.audit.log.service"
    _description = "Advance Audit Log Service"

    def log_event(self, record, event_type, description=None):

        model = self.env["ir.model"]._get(record._name)

        values = {
            "company_id": self.env.company.id,
            "user_id": self.env.user.id,
            "event_type": event_type,
            "model_id": model.id,
            "model_name": record._name,
            "record_id": record.id,
            "record_name": record.display_name,
            "description": description or "",
        }

        return self.env["advance.audit.event"].create(values)