from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _set_customer_destination(self):
        for picking in self:
            if (
                picking.picking_type_id.code == "internal"
                and picking.partner_id
                and picking.partner_id.property_stock_customer
            ):
                picking.location_dest_id = (
                    picking.partner_id.property_stock_customer
                )

    def action_confirm(self):
        res = super().action_confirm()
        self._set_customer_destination()
        return res

    def action_assign(self):
        res = super().action_assign()
        self._set_customer_destination()
        return res

    def button_validate(self):
        self._set_customer_destination()
        return super().button_validate()