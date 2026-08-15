# -*- coding: utf-8 -*-
from odoo import fields, models


class QaqcPrq(models.Model):
    """PRQ - Pre-Qualification.

    A one-time gate a new supplier must pass, per project, before any
    material from them can go through MAR. Approving a PRQ marks the
    supplier as an approved vendor for this project.
    """
    _name = 'qaqc.prq'
    _description = 'Pre-Qualification Request (PRQ)'
    _inherit = ['qaqc.document.mixin']

    _doc_type_code = 'PRQ'
    _sequence_code = 'qaqc.prq'

    supplier_id = fields.Many2one(
        'res.partner', string='Supplier', required=True,
        domain=[('supplier_rank', '>', 0)])
    scope_description = fields.Text(string='Scope of Supply / Service')

    company_profile = fields.Binary(string='Company Profile')
    company_profile_fname = fields.Char()
    financial_statement = fields.Binary(string='Financial Statement')
    financial_statement_fname = fields.Char()
    previous_projects = fields.Binary(string='Previous Projects List')
    previous_projects_fname = fields.Char()
    iso_certificates = fields.Binary(string='ISO / Quality Certificates')
    iso_certificates_fname = fields.Char()

    rejection_reason = fields.Text(string='Rejection Reason')

    def action_approve(self):
        res = super().action_approve()
        for rec in self:
            if rec.supplier_id:
                rec.supplier_id.write({'qaqc_approved_vendor': True})
        return res
