# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class QaqcDocumentMixin(models.AbstractModel):
    """Shared fields/behaviour for every QA/QC document type
    (PRQ, MAR, MES, MIR, RSN, WIR, NCR).

    Concrete models inherit this AND set:
      - _doc_type_code : short code used in the document reference,
                          e.g. 'MAR', 'PRQ', 'WIR' ...
      - _sequence_code  : ir.sequence code registered in data/qaqc_sequences.xml

    Reference format (from the real project templates):
        TH-JRP-[DOC TYPE]-[DISCIPLINE]-[SEQUENCE]   e.g. TH-JRP-MAR-CIV-0171
    Revision is tracked separately in `rev`.
    """
    _name = 'qaqc.document.mixin'
    _description = 'QA/QC Document Common Fields'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Set by each concrete model
    _doc_type_code = None
    _sequence_code = None

    name = fields.Char(
        string='Document Ref.', copy=False, readonly=True,
        default='New', tracking=True)
    project_id = fields.Many2one(
        'project.project', string='Project', required=True,
        default=lambda self: self._default_project_id())
    discipline = fields.Selection([
        ('civil', 'Civil'),
        ('arch', 'Architecture'),
        ('mech', 'Mechanical'),
        ('elec', 'Electrical'),
        ('id', 'ID'),
        ('ffe', 'FFE'),
        ('other', 'Other'),
    ], string='Discipline', required=True, default='civil', tracking=True)
    rev = fields.Integer(string='Rev', default=0, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'A - Approved'),
        ('approved_noted', 'B - Approved as Noted'),
        ('revise_resubmit', 'C - Revise & Resubmit'),
        ('rejected', 'D - Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    prepared_by_id = fields.Many2one('res.users', string='Prepared By',
                                      default=lambda self: self.env.user)
    reviewed_by_id = fields.Many2one('res.users', string='Reviewed By')
    approved_by_id = fields.Many2one('res.users', string='Approved By')

    consultant_rep_id = fields.Many2one('res.partner', string="Engineer's Representative")
    consultant_comments = fields.Text(string="Consultant's Comments")
    approval_date = fields.Date(string='Approval Date')

    active = fields.Boolean(default=True)

    def _default_project_id(self):
        return self.env.context.get('default_project_id', False)

    # ------------------------------------------------------------
    # Numbering
    # ------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self._generate_document_ref(vals)
        return super().create(vals_list)

    def _generate_document_ref(self, vals):
        """Builds TH-JRP-[TYPE]-[DISC]-[SEQ] using the project's contractor
        prefix and code, and the document's own sequence."""
        self.ensure_one() if False else None  # vals-based, no recordset yet
        project = self.env['project.project'].browse(vals.get('project_id'))
        discipline = vals.get('discipline', 'civil')
        disc_map = {
            'civil': 'CIV', 'arch': 'ARCH', 'mech': 'MECH',
            'elec': 'ELEC', 'id': 'ID', 'ffe': 'FFE', 'other': 'OTH',
        }
        disc_code = disc_map.get(discipline, 'CIV')
        seq = self.env['ir.sequence'].next_by_code(self._sequence_code) or '0000'

        prefix = project.contractor_code or 'TH'
        proj_code = project.project_code or project.name[:3].upper()
        doc_type = self._doc_type_code or 'DOC'
        return f"{prefix}-{proj_code}-{doc_type}-{disc_code}-{seq}"

    # ------------------------------------------------------------
    # Workflow actions (generic; concrete models can extend/override)
    # ------------------------------------------------------------
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Only draft documents can be submitted.")
            rec.state = 'submitted'

    def action_start_review(self):
        for rec in self:
            rec.state = 'under_review'

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved', 'approval_date': fields.Date.context_today(rec)})

    def action_approve_as_noted(self):
        for rec in self:
            rec.write({'state': 'approved_noted', 'approval_date': fields.Date.context_today(rec)})

    def action_revise_resubmit(self):
        for rec in self:
            rec.write({'state': 'revise_resubmit', 'rev': rec.rev + 1})

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
