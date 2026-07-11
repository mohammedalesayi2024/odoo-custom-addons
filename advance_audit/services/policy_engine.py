from odoo import models


class AdvanceAuditPolicyEngine(models.AbstractModel):
    _name = "advance.audit.policy.engine"
    _description = "Advance Audit Policy Engine"

    def get_policy(self, record, event_type):
        """Return the matching audit policy."""

        domain = [
            ("active", "=", True),
            ("model_id.model", "=", record._name),
        ]

        return self.env["advance.audit.policy"].search(
            domain,
            order="sequence",
            limit=1,
        )