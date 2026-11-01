import base64
import csv
import io
import hashlib
import logging
import re
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BankScannerSession(models.Model):
    _name = "bank.scanner.session"
    _description = "Bank Scanner Import Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default="New", readonly=True, copy=False, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    profile_id = fields.Many2one("bank.scanner.profile", required=True, domain="[('company_id', '=', company_id)]")
    journal_id = fields.Many2one("account.journal", related="profile_id.journal_id", store=True, readonly=True)
    file_data = fields.Binary(required=True, attachment=True)
    file_name = fields.Char(required=True)
    file_type = fields.Selection([("pdf", "PDF"), ("xlsx", "XLSX"), ("csv", "CSV")], compute="_compute_file_type", store=True)
    date_from = fields.Date()
    date_to = fields.Date()
    opening_balance = fields.Monetary(currency_field="currency_id")
    closing_balance = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="journal_id.currency_id", store=True)
    state = fields.Selection([
        ("draft", "Draft"), ("uploaded", "Uploaded"), ("scanned", "Scanned"),
        ("review", "Review"), ("ready", "Ready to Post"), ("posted", "Posted"), ("failed", "Failed")
    ], default="draft", tracking=True)
    transaction_ids = fields.One2many("bank.scanner.transaction", "session_id")
    transaction_count = fields.Integer(compute="_compute_counts")
    matched_count = fields.Integer(compute="_compute_counts")
    unmatched_count = fields.Integer(compute="_compute_counts")
    posted_count = fields.Integer(compute="_compute_counts")
    error_message = fields.Text(readonly=True)
    total_debit = fields.Monetary(compute="_compute_totals", currency_field="currency_id")
    total_credit = fields.Monetary(compute="_compute_totals", currency_field="currency_id")

    @api.depends("file_name")
    def _compute_file_type(self):
        for rec in self:
            ext = (rec.file_name or "").lower().rsplit(".", 1)[-1]
            rec.file_type = ext if ext in ("pdf", "xlsx", "csv") else False

    @api.depends("transaction_ids", "transaction_ids.match_state", "transaction_ids.state", "transaction_ids.move_id")
    def _compute_counts(self):
        for rec in self:
            lines = rec.transaction_ids
            rec.transaction_count = len(lines)
            rec.matched_count = len(lines.filtered(lambda x: x.match_state == "matched"))
            rec.unmatched_count = len(lines.filtered(lambda x: x.match_state in ("unmatched", "ambiguous")))
            rec.posted_count = len(lines.filtered(lambda x: x.move_id and x.move_id.state == "posted"))

    @api.depends("transaction_ids.debit", "transaction_ids.credit")
    def _compute_totals(self):
        for rec in self:
            rec.total_debit = sum(rec.transaction_ids.mapped("debit"))
            rec.total_credit = sum(rec.transaction_ids.mapped("credit"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("bank.scanner.session") or "New"
        return super().create(vals_list)

    def action_scan(self):
        for session in self:
            if session.state not in ("draft", "uploaded", "failed"):
                raise UserError(_("Only new or failed sessions can be scanned."))
            if not session.file_data or not session.file_name:
                raise UserError(_("Please upload a statement file."))
            session.transaction_ids.unlink()
            session.write({"state": "uploaded", "error_message": False})
            try:
                rows = session._extract_rows()
                if not rows:
                    raise UserError(_("No transaction rows were found in the uploaded file."))
                vals_list = []
                for row in rows:
                    vals = session._normalize_row(row)
                    if vals:
                        vals_list.append(vals)
                if not vals_list:
                    raise UserError(_("The file was read, but no valid transactions were extracted."))
                session.env["bank.scanner.transaction"].create([
                    dict(v, session_id=session.id, company_id=session.company_id.id) for v in vals_list
                ])
                session.write({"state": "scanned"})
                session.transaction_ids.action_strict_match()
                session.write({"state": "review"})
            except Exception as exc:
                _logger.exception("Bank Smart Scanner import failed")
                session.write({"state": "failed", "error_message": str(exc)})
                if isinstance(exc, (UserError, ValidationError)):
                    raise
                raise UserError(_("Statement processing failed: %s") % str(exc)) from exc
        return True

    def _extract_rows(self):
        self.ensure_one()
        raw = base64.b64decode(self.file_data)
        ext = (self.file_name or "").lower().rsplit(".", 1)[-1]
        profile = self.profile_id
        if ext == "csv":
            text = raw.decode(profile.encoding or "utf-8-sig", errors="replace")
            return list(csv.DictReader(io.StringIO(text), delimiter=profile.delimiter or ","))
        if ext == "xlsx":
            try:
                from openpyxl import load_workbook
            except ImportError as exc:
                raise UserError(_("XLSX import requires the Python package openpyxl on the Odoo server.")) from exc
            book = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            sheet = book.active
            values = sheet.iter_rows(values_only=True)
            headers = [str(x).strip().lower() if x is not None else "" for x in next(values, [])]
            return [dict(zip(headers, row)) for row in values if any(v is not None for v in row)]
        if ext == "pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise UserError(_("PDF text import requires pypdf on the Odoo server. Scanned PDF OCR requires a separately configured OCR service.")) from exc
            reader = PdfReader(io.BytesIO(raw))
            extracted = []
            for page_no, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                # Generic parser deliberately does not guess bank-specific table layouts.
                for line in text.splitlines():
                    parts = re.split(r"\s{2,}|\t", line.strip())
                    if len(parts) >= 3:
                        extracted.append({"_raw_line": line, "_page": page_no, "date": parts[0], "description": " ".join(parts[1:-1]), "amount": parts[-1]})
            if not extracted:
                raise UserError(_("No text transactions could be extracted from this PDF. It may be scanned or require a bank-specific PDF profile/OCR configuration."))
            return extracted
        raise UserError(_("Unsupported file type. Use PDF, XLSX, or CSV."))

    def _normalize_row(self, row):
        self.ensure_one()
        profile = self.profile_id
        def get(key, default=None):
            col = (getattr(profile, key, False) or "").strip().lower()
            if not col:
                return default
            lowered = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
            return lowered.get(col, default)
        raw_date = get("date_column") or row.get("date")
        raw_desc = get("description_column") or row.get("description") or row.get("_raw_line") or ""
        if not raw_date:
            return False
        date_value = raw_date
        if hasattr(date_value, "date"):
            date_value = date_value.date()
        if isinstance(date_value, str):
            try:
                date_value = datetime.strptime(date_value.strip(), profile.date_format or "%Y-%m-%d").date()
            except ValueError:
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"):
                    try:
                        date_value = datetime.strptime(date_value.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    raise ValidationError(_("Unsupported transaction date: %s") % raw_date)
        def amount(value):
            if value in (None, "", False):
                return 0.0
            if isinstance(value, (int, float)):
                return abs(float(value))
            cleaned = str(value).replace(",", "").replace(" ", "").replace("SAR", "").replace("ر.س", "")
            return abs(float(cleaned))
        debit_raw, credit_raw = get("debit_column"), get("credit_column")
        if debit_raw not in (None, "") or credit_raw not in (None, ""):
            debit, credit = amount(debit_raw), amount(credit_raw)
        else:
            signed = get("amount_column") or row.get("amount")
            signed_val = float(str(signed).replace(",", "").strip()) if signed not in (None, "") else 0.0
            debit, credit = (abs(signed_val), 0.0) if signed_val < 0 else (0.0, abs(signed_val))
        if not debit and not credit:
            return False
        ref = get("reference_column") or row.get("reference") or ""
        iban = get("iban_column") or row.get("iban") or ""
        partner_code = get("partner_code_column") or row.get("partner_code") or ""
        page = row.get("_page") or 0
        fingerprint_src = "|".join(map(str, [self.company_id.id, self.journal_id.id, date_value, debit, credit, ref, raw_desc]))
        fingerprint = hashlib.sha256(fingerprint_src.encode("utf-8")).hexdigest()
        return {
            "date": date_value, "description": str(raw_desc).strip(), "reference": str(ref).strip(),
            "iban": re.sub(r"\s+", "", str(iban)).upper(), "partner_code": str(partner_code).strip(),
            "debit": debit, "credit": credit, "source_page": int(page or 0),
            "raw_text": str(row.get("_raw_line") or row), "fingerprint": fingerprint,
        }
