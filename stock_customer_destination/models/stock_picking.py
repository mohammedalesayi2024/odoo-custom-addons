from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends("picking_type_id", "partner_id")
    def _compute_location_id(self):
      
        super()._compute_location_id()

        for picking in self:
            if (
                picking.state not in ("done", "cancel")
                and not picking.return_id
                and picking.picking_type_id
                and picking.picking_type_id.code == "internal"
                and picking.partner_id
                and picking.partner_id.property_stock_customer
            ):
                picking.location_dest_id = (
                    picking.partner_id.property_stock_customer
                )

    @api.onchange("partner_id", "picking_type_id")
    def _onchange_picking_type(self):
        super()._onchange_picking_type()

        if (
            self.picking_type_id
            and self.picking_type_id.code == "internal"
            and self.partner_id
            and self.partner_id.property_stock_customer
        ):
            self.location_dest_id = self.partner_id.property_stock_customer