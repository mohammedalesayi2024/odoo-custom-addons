from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

_logger.warning("######### STOCK PICKING FILE LOADED #########")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.onchange("partner_id")
    def _onchange_partner_id_set_destination_location(self):
        _logger.warning("===== ONCHANGE PARTNER =====")

        for picking in self:
            _logger.warning("Partner: %s", picking.partner_id.name)

            if (
                picking.picking_type_id
                and picking.picking_type_id.code == "internal"
                and picking.partner_id
                and picking.partner_id.property_stock_customer
            ):
                picking.location_dest_id = picking.partner_id.property_stock_customer
                _logger.warning(
                    "Destination: %s",
                    picking.location_dest_id.display_name,
                )