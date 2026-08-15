# -*- coding: utf-8 -*-
from odoo import fields, models


class QaqcMar(models.Model):
    """MAR - Material Approval Request.

    Path: Procurement -> Supplier -> QA/QC -> Document Control -> Consultant.
    Decision codes (from the real template): A-Approved, B-Approved as
    noted, C-Revise and resubmit, D-Rejected.
    """
    _name = 'qaqc.mar'
    _description = 'Material Approval Request (MAR)'
    _inherit = ['qaqc.document.mixin']

    _doc_type_code = 'MAR'
    _sequence_code = 'qaqc.mar'

    # 1. Material description
    material_description = fields.Text(string='Material Description', required=True)
    drawing_ref = fields.Char(string='Drawing Ref.')
    specification_ref = fields.Char(string='Specification Ref.')
    boq_ref = fields.Char(string='B.O.Q. Ref. No.')

    # 2. Manufacturer / Supplier
    supplier_id = fields.Many2one(
        'res.partner', string='Supplier', required=True,
        domain=[('qaqc_approved_vendor', '=', True)],
        help="Only vendors with an approved PRQ for this project can be selected.")
    manufacturer_name = fields.Char(string='Manufacturer Name')
    manufacturer_address = fields.Char(string='Manufacturer Address / P.O. Box')
    local_agent_name = fields.Char(string='Local Agent / Supplier Name')

    # 3. Delivery
    country_of_origin = fields.Char(string='Country of Origin')
    availability = fields.Selection([
        ('local', 'Locally Manufactured'),
        ('overseas', 'Overseas'),
    ], string='Availability')

    sample_required = fields.Boolean(string='Sample Required')
    sample_attached = fields.Boolean(string='Sample Attached')
    literature_required = fields.Boolean(string='Literature Required')
    literature_attached = fields.Boolean(string='Literature Attached')

    # Compliance statement
    compliance_line_ids = fields.One2many(
        'qaqc.mar.compliance.line', 'mar_id', string='Compliance Statement')

    # Additional decision flags (seen in the real MAR form footer)
    test_on_sample_required = fields.Boolean(string='Test on Sample Required')
    additional_info_required = fields.Boolean(string='Additional Information Required')
    manufacturer_guarantee_required = fields.Boolean(string="Manufacturer's Guarantee Required")

    attachment = fields.Binary(string='Technical Literature / Test Certificate')
    attachment_fname = fields.Char()


class QaqcMarComplianceLine(models.Model):
    _name = 'qaqc.mar.compliance.line'
    _description = 'MAR Compliance Statement Line'

    mar_id = fields.Many2one('qaqc.mar', string='MAR', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    contract_requirement = fields.Char(string='Contract Specification Requirement')
    compliance = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'),
    ], string='Compliance?')
    submittal_spec_ref = fields.Char(string='Submittal - Technical Specification Ref.')
