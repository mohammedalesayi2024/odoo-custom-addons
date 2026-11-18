from odoo import api, fields, models


class StockCountHistory(models.Model):
    _name = 'stock.count.history'
    _description = 'Inventory Count History'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Reference', readonly=True, index=True)
    date = fields.Datetime(string='Date', readonly=True, index=True)
    user_id = fields.Many2one('res.users', string='Counted By', readonly=True, index=True)
    reason = fields.Char(string='Inventory Reason', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True, index=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number', readonly=True)
    package_id = fields.Many2one('stock.package', string='Package', readonly=True)
    owner_id = fields.Many2one('res.partner', string='Owner', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True, index=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        related='location_id.warehouse_id', store=True, readonly=True)
    uom_id = fields.Many2one('uom.uom', string='Unit', readonly=True)
    theoretical_qty = fields.Float(
        string='Theoretical Qty', readonly=True, digits='Product Unit')
    counted_qty = fields.Float(
        string='Counted Qty', readonly=True, digits='Product Unit')
    diff_qty = fields.Float(
        string='Difference', compute='_compute_diff_qty', store=True,
        readonly=True, digits='Product Unit')
    move_id = fields.Many2one('stock.move', string='Adjustment Move', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True, index=True,
        default=lambda self: self.env.company)

    @api.depends('theoretical_qty', 'counted_qty')
    def _compute_diff_qty(self):
        for rec in self:
            rec.diff_qty = rec.counted_qty - rec.theoretical_qty
