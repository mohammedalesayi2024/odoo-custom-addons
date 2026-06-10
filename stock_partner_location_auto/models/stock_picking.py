from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('partner_id')
    def _onchange_partner_location(self):
        if self.partner_id and self.partner_id.property_stock_customer:
            self.location_dest_id = self.partner_id.property_stock_customer
