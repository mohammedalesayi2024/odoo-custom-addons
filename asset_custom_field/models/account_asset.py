from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    asset_note = fields.Char(string="Asset Note")
