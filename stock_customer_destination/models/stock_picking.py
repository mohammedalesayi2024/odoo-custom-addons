from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.onchange("partner_id")
    def _onchange_partner_id_set_destination_location(self):
        """
        عند اختيار العميل في التحويل الداخلي يتم تحديث
        موقع الوجهة مباشرة إلى موقع العميل.
        """
        for picking in self:
            if (
                picking.picking_type_id
                and picking.picking_type_id.code == "internal"
                and picking.partner_id
                and picking.partner_id.property_stock_customer
            ):
                picking.location_dest_id = (
                    picking.partner_id.property_stock_customer
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for picking in records:
            if (
                picking.picking_type_id.code == "internal"
                and picking.partner_id
                and picking.partner_id.property_stock_customer
            ):
                picking.location_dest_id = (
                    picking.partner_id.property_stock_customer
                )

        return records

    def write(self, vals):
        res = super().write(vals)

        if "partner_id" in vals:
            for picking in self:
                if (
                    picking.picking_type_id.code == "internal"
                    and picking.partner_id
                    and picking.partner_id.property_stock_customer
                ):
                    picking.location_dest_id = (
                        picking.partner_id.property_stock_customer
                    )

        return res