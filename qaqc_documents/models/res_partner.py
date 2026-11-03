# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    qaqc_approved_vendor = fields.Boolean(
        string='QA/QC Approved Vendor (Legacy)',
        help='Legacy global flag. New MAR validation uses project-specific PRQ approval.',
    )
    qaqc_contractor_code = fields.Char(
        string='QA/QC Contractor Code',
        help='Short code used at the beginning of QA/QC document references when this contact is the project contractor (e.g. WM).',
    )
