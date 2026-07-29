from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    Asset_Location = fields.Char(string="Asset Location")
