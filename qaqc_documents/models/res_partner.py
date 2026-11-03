from odoo import fields, models
class ResPartner(models.Model):
    _inherit='res.partner'
    qaqc_approved_vendor=fields.Boolean(string='QA/QC Approved Vendor (Legacy)',help='Legacy global flag. New MAR validation uses project-specific PRQ approval.')
