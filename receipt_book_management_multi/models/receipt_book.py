from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReceiptBook(models.Model):
    _name = "receipt.book.multi"
    _description = "Receipt Book"
    _order = "id desc"

    name = fields.Char(
        string="Receipt Book",
        required=True,
    )

    salesperson_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        required=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    from_number = fields.Integer(
        string="From Number",
        required=True,
    )

    to_number = fields.Integer(
        string="To Number",
        required=True,
    )

    next_number = fields.Integer(
        string="Next Number",
        required=True,
    )

    issue_date = fields.Date(
        string="Issue Date",
        default=fields.Date.today,
    )

    notes = fields.Text()

    total_receipts = fields.Integer(
        string="Total Receipts",
        compute="_compute_totals",
        store=True,
    )

    remaining = fields.Integer(
        string="Remaining",
        compute="_compute_totals",
        store=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("finished", "Finished"),
        ],
        string="Status",
        compute="_compute_state",
        store=True,
    )

    received_by_accountant = fields.Boolean(
        string="Received by Accountant",
        copy=False,
        default=False,
    )

    _sql_constraints = [
        (
            "receipt_book_multi_name_company_unique",
            "unique(name, company_id)",
            "Receipt Book name must be unique per company.",
        ),
    ]

    @api.depends("from_number", "to_number", "next_number")
    def _compute_totals(self):
        for rec in self:
            if rec.from_number and rec.to_number:
                rec.total_receipts = rec.to_number - rec.from_number + 1
            else:
                rec.total_receipts = 0

            if rec.next_number:
                rec.remaining = max(rec.to_number - rec.next_number + 1, 0)
            else:
                rec.remaining = 0

    @api.depends("from_number", "to_number", "next_number")
    def _compute_state(self):
        for rec in self:

            if rec.next_number > rec.to_number:
                rec.state = "finished"

            elif rec.next_number == rec.from_number:
                rec.state = "draft"

            else:
                rec.state = "active"

    @api.constrains("from_number", "to_number")
    def _check_range(self):
        for rec in self:
            if rec.from_number <= 0:
                raise ValidationError(
                    _("The starting number must be greater than zero.")
                )

            if rec.to_number <= rec.from_number:
                raise ValidationError(
                    _("The ending number must be greater than the starting number.")
                )

    @api.constrains("next_number", "from_number", "to_number")
    def _check_next_number(self):
        for rec in self:
            if rec.next_number < rec.from_number:
                raise ValidationError(
                    _("Next Number cannot be less than the starting number.")
                )

            if rec.next_number > rec.to_number + 1:
                raise ValidationError(
                    _("Next Number cannot exceed the receipt book range.")
                )

    @api.constrains("salesperson_id", "state", "from_number", "to_number", "company_id")
    def _check_active_book(self):
        # Multiple unfinished receipt books are allowed for the same salesperson.
        # Only overlapping receipt-number ranges are rejected.
        for rec in self:
            if rec.state == "finished":
                continue

            books = self.search([
                ("id", "!=", rec.id),
                ("salesperson_id", "=", rec.salesperson_id.id),
                ("company_id", "=", rec.company_id.id),
                ("state", "!=", "finished"),
                ("from_number", "<=", rec.to_number),
                ("to_number", ">=", rec.from_number),
            ], limit=1)

            if books:
                raise ValidationError(
                    _("The receipt number range overlaps with another Receipt Book for this salesperson. Please use a different number range.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("next_number") and vals.get("from_number"):
                vals["next_number"] = vals["from_number"]

        return super().create(vals_list)