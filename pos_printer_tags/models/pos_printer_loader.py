from odoo import models


class PosPrinter(models.Model):
    _inherit = "pos.printer"

    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)

        fields += [
            "routing_method",
            "printed_product_tag_ids",
        ]

        return fields