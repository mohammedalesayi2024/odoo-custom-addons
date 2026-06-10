from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    voucher_footer = fields.Text(
        string="Voucher Footer"
    )

    voucher_stamp = fields.Image(
        string="Company Stamp"
    )

    voucher_signature = fields.Image(
        string="Authorized Signature"
    )

    voucher_show_qr = fields.Boolean(
        string="Show QR Code",
        default=True
    )

    voucher_show_time = fields.Boolean(
        string="Show Time",
        default=True
    )