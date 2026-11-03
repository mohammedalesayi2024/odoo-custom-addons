# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class QaqcPrq(models.Model):
    _name = 'qaqc.prq'
    _description = 'Pre-Qualification Request (PRQ)'
    _inherit = ['qaqc.document.mixin']
    _doc_type_code = 'PRQ'
    _sequence_code = 'qaqc.prq'
    attachment_ids = fields.Many2many('ir.attachment', 'qaqc_prq_attachment_rel', 'document_id', 'attachment_id', string='Attachments', copy=False)
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, domain=[('supplier_rank','>',0)])
    scope_description = fields.Text(string='Scope of Supply / Service')
    company_profile = fields.Binary(attachment=True); company_profile_fname = fields.Char()
    financial_statement = fields.Binary(attachment=True); financial_statement_fname = fields.Char()
    previous_projects = fields.Binary(attachment=True); previous_projects_fname = fields.Char()
    iso_certificates = fields.Binary(attachment=True); iso_certificates_fname = fields.Char()
    rejection_reason = fields.Text()
    def action_consultant_approve_noted(self):
        result = super().action_consultant_approve_noted()
        self._register_approved_suppliers()
        return result

    def _register_approved_suppliers(self):
        for rec in self:
            link = self.env['qaqc.approved.vendor'].search([('project_id','=',rec.project_id.id),('supplier_id','=',rec.supplier_id.id)],limit=1)
            if not link: self.env['qaqc.approved.vendor'].create({'project_id':rec.project_id.id,'supplier_id':rec.supplier_id.id,'prq_id':rec.id})

    def action_consultant_approve(self):
        result = super().action_consultant_approve()
        self._register_approved_suppliers()
        return result

class QaqcApprovedVendor(models.Model):
    _name = 'qaqc.approved.vendor'
    _description = 'Approved Supplier per Project'
    _rec_name = 'supplier_id'
    _sql_constraints = [('project_supplier_unique','unique(project_id,supplier_id)','This supplier is already approved for this project.')]
    project_id = fields.Many2one('project.project',required=True,ondelete='cascade')
    supplier_id = fields.Many2one('res.partner',required=True,ondelete='restrict')
    prq_id = fields.Many2one('qaqc.prq',required=True,ondelete='restrict')
    approved_on = fields.Date(default=fields.Date.context_today)
