from odoo import models


class AdvanceAuditLogService(models.AbstractModel):
    _name = "advance.audit.log.service"
    _description = "Advance Audit Log Service"

    def log_create(self, record):
        """Log create operation."""
        pass

    def log_write(self, record, old_values):
        """Log write operation."""
        pass

    def log_delete(self, record):
        """Log delete operation."""
        pass