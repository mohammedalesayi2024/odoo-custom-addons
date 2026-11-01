from odoo import fields, models


class BankScannerProfile(models.Model):
    _name = "bank.scanner.profile"
    _description = "Bank Scanner Import Profile"
    _order = "name"

    name = fields.Char(required=True)
    bank_name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    journal_id = fields.Many2one(
        "account.journal", required=True,
        domain="[('type', '=', 'bank'), ('company_id', '=', company_id)]",
    )
    currency_id = fields.Many2one("res.currency", related="journal_id.currency_id", store=True, readonly=True)
    active = fields.Boolean(default=True)
    file_format = fields.Selection([
        ("auto", "Auto Detect"), ("pdf", "PDF"), ("xlsx", "Excel XLSX"), ("csv", "CSV")
    ], default="auto", required=True)
    date_format = fields.Char(default="%Y-%m-%d", help="Python strptime format for imported dates.")
    delimiter = fields.Char(default=",")
    encoding = fields.Char(default="utf-8-sig")
    date_column = fields.Char(default="date")
    description_column = fields.Char(default="description")
    debit_column = fields.Char(default="debit")
    credit_column = fields.Char(default="credit")
    amount_column = fields.Char(default="amount", help="Used when debit/credit columns are not present.")
    reference_column = fields.Char(default="reference")
    iban_column = fields.Char(default="iban")
    partner_code_column = fields.Char(default="partner_code")
    expense_account_id = fields.Many2one("account.account", domain="[('company_ids', 'in', company_id)]")
