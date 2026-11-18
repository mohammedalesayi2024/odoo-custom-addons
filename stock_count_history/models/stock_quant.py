from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def action_apply_inventory(self):
        # 1) Snapshot BEFORE the standard apply, while the theoretical qty is intact.
        start = fields.Datetime.now()
        snapshot = []
        for quant in self.filtered('inventory_quantity_set'):
            snapshot.append({
                'quant': quant,
                'vals': {
                    'user_id': self.env.user.id,
                    'reason': self.env.context.get('inventory_name') or False,
                    'product_id': quant.product_id.id,
                    'lot_id': quant.lot_id.id,
                    'package_id': quant.package_id.id,
                    'owner_id': quant.owner_id.id,
                    'location_id': quant.location_id.id,
                    'uom_id': quant.product_uom_id.id,
                    'theoretical_qty': quant.quantity,
                    'counted_qty': quant.inventory_quantity,
                    'company_id': quant.company_id.id or self.env.company.id,
                },
            })

        res = super().action_apply_inventory()

        # 2) Log only what was really applied (standard may return a wizard
        #    instead of applying, e.g. tracked product without lot).
        applied = [
            s for s in snapshot
            if not s['quant'].exists() or not s['quant'].inventory_quantity_set
        ]
        if not applied:
            return res

        reference = self.env['ir.sequence'].sudo().next_by_code('stock.count.history') or '/'
        now = fields.Datetime.now()

        # Best-effort link to the adjustment moves created by the standard apply.
        move_lines = self.env['stock.move.line'].sudo().search([
            ('is_inventory', '=', True),
            ('product_id', 'in', [s['vals']['product_id'] for s in applied]),
            ('date', '>=', start),
        ], order='id desc')

        vals_list = []
        for s in applied:
            vals = dict(s['vals'], name=reference, date=now)
            for ml in move_lines:
                if (ml.product_id.id == vals['product_id']
                        and ml.lot_id.id == vals['lot_id']
                        and vals['location_id'] in (ml.location_id.id, ml.location_dest_id.id)):
                    vals['move_id'] = ml.move_id.id
                    break
            vals_list.append(vals)

        self.env['stock.count.history'].sudo().create(vals_list)
        return res
