# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    loyalty_card_ids = fields.One2many(
        "loyalty.card", "partner_id", string="بطاقات الولاء"
    )
    total_loyalty_points = fields.Float(
        string="إجمالي نقاط الولاء",
        compute="_compute_total_loyalty_points",
    )

    @api.depends("loyalty_card_ids", "loyalty_card_ids.points")
    def _compute_total_loyalty_points(self):
        for partner in self:
            cards = partner.loyalty_card_ids.filtered(
                lambda c: c.program_id.program_type == "loyalty"
            )
            partner.total_loyalty_points = sum(cards.mapped("points"))

    def action_open_point_to_coupon_wizard(self):
        """يفتح المعالج (Wizard) الخاص بتحويل النقاط إلى كوبون."""
        self.ensure_one()
        loyalty_cards = self.loyalty_card_ids.filtered(
            lambda c: c.program_id.program_type == "loyalty" and c.points > 0
        )
        return {
            "type": "ir.actions.act_window",
            "name": "تحويل نقاط الولاء إلى كوبون",
            "res_model": "loyalty.point.to.coupon.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_loyalty_card_id": loyalty_cards[:1].id,
            },
        }
