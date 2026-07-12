from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceiptBook(models.Model):
    _name = "receipt.book"
    _description = "Receipt Book"
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(
        string="Book Name",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        required=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
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

    warning_limit = fields.Integer(
        string="Warning Limit",
        default=10,
    )

    remaining = fields.Integer(
        string="Remaining",
        compute="_compute_remaining",
        store=True,
    )

    state = fields.Selection(
        [
            ("active", "Active"),
            ("near_end", "Near End"),
            ("finished", "Finished"),
        ],
        string="Status",
        compute="_compute_state",
        store=True,
    )

    active = fields.Boolean(
        default=True,
    )

    @api.depends("next_number", "to_number")
    def _compute_remaining(self):
        for rec in self:
            rec.remaining = max(rec.to_number - rec.next_number + 1, 0)

    @api.depends("remaining", "warning_limit")
    def _compute_state(self):
        for rec in self:

            if rec.remaining == 0:
                rec.state = "finished"

            elif rec.remaining <= rec.warning_limit:
                rec.state = "near_end"

            else:
                rec.state = "active"

    @api.constrains("from_number", "to_number", "next_number")
    def _check_numbers(self):
        for rec in self:

            if rec.from_number <= 0:
                raise ValidationError("From Number must be greater than zero.")

            if rec.to_number < rec.from_number:
                raise ValidationError("To Number must be greater than From Number.")

            if rec.next_number < rec.from_number:
                raise ValidationError("Next Number cannot be less than From Number.")

            if rec.next_number > rec.to_number + 1:
                raise ValidationError("Next Number exceeds the book range.")