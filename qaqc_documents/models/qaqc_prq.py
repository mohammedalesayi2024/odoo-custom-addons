# -*- coding: utf-8 -*-
from odoo import fields, models


class QaqcPrq(models.Model):
    _name = 'qaqc.prq'
    _description = 'Pre-Qualification Request (PRQ)'
    _inherit = ['qaqc.document.mixin']
    _doc_type_code = 'PRQ'
    _sequence_code = 'qaqc.prq'

    attachment_ids = fields.Many2many(
        'ir.attachment', 'qaqc_prq_attachment_rel', 'document_id', 'attachment_id',
        string='Attachments', copy=False,
    )
    supplier_id = fields.Many2one(
        'res.partner', string='Supplier', required=True,
        domain=[('supplier_rank', '>', 0)], tracking=True,
        help='Select a vendor already registered in Odoo Contacts/Accounting. PRQ approval is project-specific and does not deactivate the vendor in Accounting.',
    )
    scope_description = fields.Text(string='Scope of Supply / Service')
    employer_id = fields.Many2one(related='project_id.employer_id', string='Employer', readonly=True)
    engineer_id = fields.Many2one(related='project_id.engineer_id', string='Engineer / Consultant', readonly=True)
    contractor_id = fields.Many2one(related='project_id.contractor_id', string='Contractor', readonly=True)
    company_profile = fields.Binary(attachment=True); company_profile_fname = fields.Char()
    financial_statement = fields.Binary(attachment=True); financial_statement_fname = fields.Char()
    previous_projects = fields.Binary(attachment=True); previous_projects_fname = fields.Char()
    iso_certificates = fields.Binary(attachment=True); iso_certificates_fname = fields.Char()
    rejection_reason = fields.Text()
    supplier_project_status = fields.Selection([
        ('not_approved', 'Not Approved'),
        ('approved', 'Approved for this Project'),
    ], string='Supplier Project Approval', compute='_compute_supplier_project_status')

    def _compute_supplier_project_status(self):
        approved_model = self.env['qaqc.approved.vendor']
        for rec in self:
            is_approved = bool(rec.project_id and rec.supplier_id and approved_model.search_count([
                ('project_id', '=', rec.project_id.id),
                ('supplier_id', '=', rec.supplier_id.id),
                ('active', '=', True),
            ]))
            rec.supplier_project_status = 'approved' if is_approved else 'not_approved'

    def _consultant_decide(self, decision):
        result = super()._consultant_decide(decision)
        for rec in self:
            link = self.env['qaqc.approved.vendor'].search([
                ('project_id', '=', rec.project_id.id),
                ('supplier_id', '=', rec.supplier_id.id),
            ], limit=1)
            if decision in ('A', 'B'):
                if link:
                    link.write({'active': True, 'prq_id': rec.id, 'approved_on': fields.Date.context_today(self)})
                else:
                    self.env['qaqc.approved.vendor'].create({
                        'project_id': rec.project_id.id,
                        'supplier_id': rec.supplier_id.id,
                        'prq_id': rec.id,
                        'active': True,
                    })
            elif decision in ('C', 'D') and link:
                link.write({'active': False})
        return result


class QaqcApprovedVendor(models.Model):
    _name = 'qaqc.approved.vendor'
    _description = 'Approved Supplier per Project'
    _rec_name = 'supplier_id'
    _sql_constraints = [
        ('project_supplier_unique', 'unique(project_id,supplier_id)',
         'This supplier already has an approval record for this project.'),
    ]
    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)
    supplier_id = fields.Many2one('res.partner', required=True, ondelete='restrict', index=True)
    prq_id = fields.Many2one('qaqc.prq', required=True, ondelete='restrict')
    approved_on = fields.Date(default=fields.Date.context_today)
    active = fields.Boolean(default=True, index=True)
