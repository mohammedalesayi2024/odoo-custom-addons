from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    voucher_footer = fields.Text(
        related="company_id.voucher_footer",
        readonly=False
    )

    voucher_stamp = fields.Image(
        related="company_id.voucher_stamp",
        readonly=False
    )

    voucher_signature = fields.Image(
        related="company_id.voucher_signature",
        readonly=False
    )

    voucher_show_qr = fields.Boolean(
        related="company_id.voucher_show_qr",
        readonly=False
    )

    voucher_show_time = fields.Boolean(
        related="company_id.voucher_show_time",
        readonly=False
    )