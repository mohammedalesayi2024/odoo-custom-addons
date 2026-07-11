from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        # Ignore Advance Audit models
        if self._name.startswith("advance.audit"):
            return records

        try:
            audit = self.env["advance.audit.log.service"]
            
            for record in records:
                try:
                    audit.log_event(
                        record=record,
                        event_type="create",
                        description="Record created",
                    )
                except Exception as e:
                    # Log the error but don't break the transaction
                    self.env.logger.warning(
                        f"Failed to log audit event for {self._name}: {str(e)}"
                    )
        except Exception as e:
            self.env.logger.error(f"Audit service error: {str(e)}")

        return records