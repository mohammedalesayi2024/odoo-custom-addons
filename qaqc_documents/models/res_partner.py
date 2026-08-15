# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    qaqc_approved_vendor = fields.Boolean(
        string='QA/QC Approved Vendor', copy=False,
        help="Set automatically when a PRQ for this supplier is approved.")
