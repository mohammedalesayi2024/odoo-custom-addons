from odoo import fields, models


class BulkFIFOSettingsWizard(models.TransientModel):
    _name = "bulk.fifo.settings.wizard"
    _description = "Bulk FIFO Settings Wizard"

    auto_fifo_reconcile = fields.Boolean(
        string="التسوية التلقائية",
        default=True,
    )

    payment_allocation_method = fields.Selection(
        [
            ("date", "حسب تاريخ المعاملة"),
            ("due_date", "حسب تاريخ الاستحقاق"),
        ],
        string="آلية توزيع الدفعة",
        default="date",
        required=True,
    )

    def action_apply(self):
        partner_ids = self.env.context.get("active_ids", [])
        partners = self.env["res.partner"].browse(partner_ids)

        values = {
            "auto_fifo_reconcile": self.auto_fifo_reconcile,
        }

        if self.auto_fifo_reconcile:
            values["payment_allocation_method"] = self.payment_allocation_method

        partners.write(values)

        return {"type": "ir.actions.act_window_close"}