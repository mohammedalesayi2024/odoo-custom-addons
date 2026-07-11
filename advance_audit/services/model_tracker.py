from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def create(self, vals_list):
        return super().create(vals_list)