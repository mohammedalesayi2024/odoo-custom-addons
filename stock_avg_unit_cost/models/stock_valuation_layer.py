from odoo import models, fields, api


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    x_avg_unit_cost = fields.Float(
        string='Avg Unit Cost',
        compute='_compute_avg_unit_cost',
        store=False,
        group_operator='avg',
    )

    @api.depends('value', 'quantity')
    def _compute_avg_unit_cost(self):

        for record in self:

            if record.quantity:
                record.x_avg_unit_cost = (
                    record.value / record.quantity
                )
            else:
                record.x_avg_unit_cost = 0