from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        # Ignore Advance Audit models
        if self._name.startswith("advance.audit"):
            return records

        audit = self.env["advance.audit.log.service"]

        for record in records:
            audit.log_event(
                record=record,
                event_type="create",
                 description="Record created",
            )

        return records