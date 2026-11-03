# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
class QaqcMar(models.Model):
    _name = 'qaqc.mar'; _description = 'Material Approval Request (MAR)'; _inherit = ['qaqc.document.mixin']
    _doc_type_code = 'MAR'; _sequence_code = 'qaqc.mar'
    attachment_ids = fields.Many2many('ir.attachment', 'qaqc_mar_attachment_rel', 'document_id', 'attachment_id', string='Attachments', copy=False)
    material_description = fields.Text(required=True); drawing_ref = fields.Char(); specification_ref = fields.Char(); boq_ref = fields.Char()
    supplier_id = fields.Many2one('res.partner',string='Supplier',required=True,domain="[('id','in',approved_supplier_ids)]")
    approved_supplier_ids = fields.Many2many('res.partner',compute='_compute_approved_supplier_ids')
    @api.depends('project_id')
    def _compute_approved_supplier_ids(self):
        for rec in self: rec.approved_supplier_ids = self.env['qaqc.approved.vendor'].search([('project_id','=',rec.project_id.id),('active','=',True)]).mapped('supplier_id')
    @api.constrains('project_id','supplier_id')
    def _check_supplier_project_approval(self):
        for rec in self:
            if rec.supplier_id and not self.env['qaqc.approved.vendor'].search_count([('project_id','=',rec.project_id.id),('supplier_id','=',rec.supplier_id.id),('active','=',True)]):
                raise ValidationError('The supplier must have an approved PRQ in this project before creating a MAR.')
    manufacturer_name = fields.Char(); manufacturer_address = fields.Char(); local_agent_name = fields.Char()
    country_of_origin = fields.Char()
    availability = fields.Selection([('local','Local'),('overseas','Imported')])
    sample_required = fields.Boolean(); sample_attached = fields.Boolean(); literature_required = fields.Boolean(); literature_attached = fields.Boolean()
    test_on_sample_required = fields.Boolean(); additional_info_required = fields.Boolean(); manufacturer_guarantee_required = fields.Boolean()
    technical_data_sheet = fields.Binary(attachment=True); technical_data_sheet_fname = fields.Char()
    test_report = fields.Binary(attachment=True); test_report_fname = fields.Char()
    compliance_statement = fields.Binary(attachment=True); compliance_statement_fname = fields.Char()
    compliance_line_ids = fields.One2many('qaqc.mar.compliance.line','mar_id')
class QaqcMarComplianceLine(models.Model):
    _name = 'qaqc.mar.compliance.line'; _description = 'MAR Compliance Statement Line'; _order = 'sequence,id'
    mar_id = fields.Many2one('qaqc.mar',required=True,ondelete='cascade'); sequence = fields.Integer(default=10)
    contract_requirement = fields.Char(); compliance = fields.Selection([('yes','Yes'),('no','No')]); submittal_spec_ref = fields.Char()
