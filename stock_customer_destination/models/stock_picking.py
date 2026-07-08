from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.onchange("partner_id")
    def _onchange_partner_id_set_destination_location(self):
        for picking in self:
            if (
                picking.picking_type_id
                and picking.picking_type_id.code == "internal"
                and picking.partner_id
                and picking.partner_id.property_stock_customer
            ):
                picking.update({
                    "location_dest_id": picking.partner_id.property_stock_customer.id,
                })