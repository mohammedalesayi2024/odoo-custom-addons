from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    qaqc_approved_vendor = fields.Boolean(
        string='QA/QC Approved Vendor', copy=False, tracking=True,
        help='Enabled by the PRQ workflow after final approval. This is an overall flag, not a per-project approval.')
