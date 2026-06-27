# -*- coding: utf-8 -*-

from odoo import fields, models


class PosPrinter(models.Model):
    _inherit = "pos.printer"

    printed_product_tag_ids = fields.Many2many(
        comodel_name="product.tag",
        relation="pos_printer_product_tag_rel",
        column1="printer_id",
        column2="tag_id",
        string="Printed Product Tags",
        help="Products with these tags will be printed on this printer.",
    )