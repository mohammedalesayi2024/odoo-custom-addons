from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BankScannerTransaction(models.Model):
    _name = "bank.scanner.transaction"
    _description = "Imported Bank Transaction"
    _order = "date, id"

    session_id = fields.Many2one("bank.scanner.session", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one("res.company", required=True, index=True)
    date = fields.Date(required=True, index=True)
    description = fields.Char(required=True)
    reference = fields.Char(index=True)
    iban = fields.Char(index=True)
    partner_code = fields.Char()
    debit = fields.Monetary(currency_field="currency_id")
    credit = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="session_id.currency_id", store=True)
    source_page = fields.Integer()
    raw_text = fields.Text()
    fingerprint = fields.Char(index=True, required=True)
    transaction_type = fields.Selection([
        ("customer_deposit", "Customer Deposit"), ("vendor_transfer", "Vendor Transfer"),
        ("bank_charge", "Bank Charges"), ("internal_transfer", "Internal Transfer"),
        ("other", "Other"), ("unknown", "Unknown")
    ], default="unknown", required=True)
    partner_id = fields.Many2one("res.partner", index=True)
    counterpart_account_id = fields.Many2one("account.account", domain="[ ('company_ids', 'in', company_id) ]", help="Optional explicitly selected counterpart account for this transaction.")
    match_state = fields.Selection([
        ("unmatched", "Unmatched"), ("matched", "Matched"), ("ambiguous", "Ambiguous"),
        ("manual", "Manually Confirmed"), ("rejected", "Rejected")
    ], default="unmatched")
    match_note = fields.Char()
    state = fields.Selection([
        ("new", "New"), ("approved", "Approved"), ("excluded", "Excluded"), ("posted", "Posted")
    ], default="new")
    move_id = fields.Many2one("account.move", readonly=True, copy=False)
    duplicate_of_id = fields.Many2one("bank.scanner.transaction", readonly=True)

    @api.constrains("debit", "credit")
    def _check_single_direction(self):
        for rec in self:
            if rec.debit and rec.credit:
                raise ValidationError(_("A transaction cannot have both debit and credit amounts."))

    def action_strict_match(self):
        for rec in self:
            if rec.iban:
                # Compare normalized account numbers in Python for compatibility across Odoo versions.
                accounts = self.env["res.partner.bank"].search([("partner_id", "!=", False)])
                normalized = lambda value: "".join(ch for ch in (value or "").upper() if ch.isalnum())
                partners = accounts.filtered(lambda account: normalized(account.acc_number) == normalized(rec.iban)).mapped("partner_id")
            elif rec.partner_code:
                # Strict code matching only when an exact partner reference exists.
                partners = self.env["res.partner"].search([("ref", "=", rec.partner_code)], limit=2)
            else:
                partners = self.env["res.partner"]
            if len(partners) == 1:
                rec.write({"partner_id": partners.id, "match_state": "matched", "match_note": _("Exact identifier match")})
            elif len(partners) > 1:
                rec.write({"match_state": "ambiguous", "match_note": _("More than one partner matches the supplied identifier.")})
            else:
                rec.write({"match_state": "unmatched", "match_note": _("No exact partner identifier was found. Name similarity is not used.")})
            duplicates = self.search([
                ("id", "!=", rec.id), ("company_id", "=", rec.company_id.id),
                ("session_id.journal_id", "=", rec.session_id.journal_id.id),
                ("fingerprint", "=", rec.fingerprint),
            ], limit=1)
            if duplicates:
                rec.write({"duplicate_of_id": duplicates.id, "match_state": "rejected", "match_note": _("Potential duplicate of %s") % duplicates.display_name})
        return True

    def action_approve(self):
        for rec in self:
            if rec.match_state not in ("matched", "manual") and rec.transaction_type not in ("bank_charge", "internal_transfer"):
                raise UserError(_("Only strictly matched or manually confirmed transactions can be approved."))
            if rec.duplicate_of_id:
                raise UserError(_("Potential duplicate transactions cannot be approved."))
            rec.state = "approved"
        return True

    def action_exclude(self):
        self.write({"state": "excluded"})
        return True

    def action_create_draft_move(self):
        for rec in self:
            if rec.state != "approved":
                raise UserError(_("Approve the transaction before generating its journal entry."))
            if rec.move_id:
                continue
            journal = rec.session_id.journal_id
            company = rec.company_id
            bank_account = journal.default_account_id
            if not bank_account:
                raise UserError(_("The selected bank journal has no default account configured."))
            if rec.debit:
                # Bank statement debit is an outgoing payment.
                counterpart = rec.counterpart_account_id
                if not counterpart and rec.partner_id:
                    counterpart = rec.partner_id.property_account_payable_id
                if not counterpart:
                    counterpart = rec.session_id.profile_id.expense_account_id
                if not counterpart:
                    raise UserError(_("No payable or configured expense account is available for this debit transaction."))
                lines = [
                    (0, 0, {"name": rec.description, "account_id": counterpart.id, "partner_id": rec.partner_id.id if rec.partner_id else False, "debit": rec.debit, "credit": 0.0}),
                    (0, 0, {"name": rec.description, "account_id": bank_account.id, "debit": 0.0, "credit": rec.debit}),
                ]
            else:
                if not rec.partner_id:
                    raise UserError(_("A strictly identified partner is required for incoming deposits."))
                counterpart = rec.counterpart_account_id or rec.partner_id.property_account_receivable_id
                if not counterpart:
                    raise UserError(_("The selected partner has no receivable account."))
                lines = [
                    (0, 0, {"name": rec.description, "account_id": bank_account.id, "debit": rec.credit, "credit": 0.0}),
                    (0, 0, {"name": rec.description, "account_id": counterpart.id, "partner_id": rec.partner_id.id, "debit": 0.0, "credit": rec.credit}),
                ]
            move = self.env["account.move"].create({
                "move_type": "entry", "date": rec.date, "journal_id": journal.id,
                "ref": rec.reference or rec.description,
                "company_id": company.id, "line_ids": lines,
            })
            rec.move_id = move.id
        return True

    def action_post_draft_move(self):
        for rec in self:
            if not rec.move_id:
                raise UserError(_("Generate the draft journal entry first."))
            if rec.move_id.state != "draft":
                raise UserError(_("The linked journal entry is not in Draft state."))
            rec.move_id.action_post()
            rec.state = "posted"
        return True
