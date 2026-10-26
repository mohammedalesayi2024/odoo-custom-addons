from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class QaqcPrqWorkflow(models.Model):
    _name = 'qaqc.prq.workflow'
    _description = 'PRQ Approval Workflow Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade', tracking=True,
        help='Leave empty for a general PRQ workflow. Project-specific configuration takes precedence.')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    step_ids = fields.One2many('qaqc.prq.workflow.step', 'workflow_id', string='Approval Steps', copy=True)
    step_count = fields.Integer(compute='_compute_step_count')

    @api.depends('step_ids')
    def _compute_step_count(self):
        for rec in self:
            rec.step_count = len(rec.step_ids)

    @api.constrains('project_id', 'company_id')
    def _check_unique_project_company(self):
        for rec in self:
            domain = [('id', '!=', rec.id), ('company_id', '=', rec.company_id.id), ('active', '=', True)]
            domain += [('project_id', '=', rec.project_id.id)] if rec.project_id else [('project_id', '=', False)]
            if self.search_count(domain):
                raise ValidationError(_('Only one active PRQ workflow is allowed per project (or one general workflow) and company.'))

class QaqcPrqWorkflowStep(models.Model):
    _name = 'qaqc.prq.workflow.step'
    _description = 'PRQ Approval Workflow Step'
    _order = 'sequence, id'

    workflow_id = fields.Many2one('qaqc.prq.workflow', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10, required=True)
    name = fields.Char(required=True)
    role = fields.Selection([('review', 'Review'), ('approve', 'Final/Stage Approval')], required=True, default='review')
    user_id = fields.Many2one('res.users', string='Specific Responsible User',
        domain=[('share', '=', False)], help='If set, only this user can action this step (or a QA/QC manager).')
    group_id = fields.Many2one('res.groups', string='Responsible Group',
        help='If no specific user is selected, a member of this group can action the step.')
    required = fields.Boolean(default=True)

    @api.constrains('user_id', 'group_id')
    def _check_assignee(self):
        for rec in self:
            if not rec.user_id and not rec.group_id:
                raise ValidationError(_('Each workflow step must have a specific user or a responsible group.'))

class QaqcPrqApproval(models.Model):
    _name = 'qaqc.prq.approval'
    _description = 'PRQ Approval History'
    _order = 'sequence, id'

    prq_id = fields.Many2one('qaqc.prq', required=True, ondelete='cascade', index=True)
    run_number = fields.Integer(required=True, default=1, index=True)
    sequence = fields.Integer(required=True)
    step_name = fields.Char(required=True)
    role = fields.Selection([('review', 'Review'), ('approve', 'Final/Stage Approval')], required=True)
    assigned_user_id = fields.Many2one('res.users', string='Assigned User')
    assigned_group_id = fields.Many2one('res.groups', string='Assigned Group')
    state = fields.Selection([
        ('pending', 'Pending'), ('approved', 'Approved'), ('returned', 'Returned for Changes'),
        ('rejected', 'Rejected'), ('skipped', 'Skipped')], default='pending', required=True)
    decision = fields.Selection([('approve', 'Approve / Complete'), ('return', 'Return for Changes'), ('reject', 'Reject')])
    comments = fields.Text()
    decision_by_id = fields.Many2one('res.users', readonly=True)
    decision_date = fields.Datetime(readonly=True)

    def write(self, vals):
        decision_fields = {'state', 'decision', 'comments', 'decision_by_id', 'decision_date'}
        if decision_fields.intersection(vals) and not self.env.context.get('qaqc_approval_action'):
            raise UserError(_('Approval decisions can only be recorded through the PRQ workflow actions.'))
        if any(rec.state != 'pending' for rec in self) and decision_fields.intersection(vals):
            raise UserError(_('A completed approval decision is immutable. Create a new revision or workflow run instead.'))
        return super().write(vals)
