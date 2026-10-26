import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class QaqcPrq(models.Model):
    _name = 'qaqc.prq'
    _description = 'Supplier Pre-Qualification Request (PRQ)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Document Reference', required=True, copy=False, readonly=True, default='New', tracking=True)
    project_id = fields.Many2one('project.project', required=True, tracking=True, index=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier / Subcontractor', required=True, tracking=True,
        domain=[('supplier_rank', '>', 0)])
    discipline = fields.Selection([('civil','Civil'),('architecture','Architecture'),('mechanical','Mechanical'),
        ('electrical','Electrical'),('id','Interior Design'),('ffe','FFE'),('other','Other')], required=True, default='civil', tracking=True)
    scope_description = fields.Text(string='Scope of Supply / Service', required=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    revision = fields.Integer(default=0, readonly=True, copy=False, tracking=True)
    state = fields.Selection([
        ('draft','Draft'), ('submitted','Submitted'), ('under_review','Under Review'),
        ('revise_resubmit','Returned for Changes'), ('approved','Approved'), ('rejected','Rejected'), ('cancelled','Cancelled')],
        default='draft', required=True, copy=False, tracking=True, index=True)
    prepared_by_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True, tracking=True)
    current_approval_id = fields.Many2one('qaqc.prq.approval', compute='_compute_current_approval', store=False)
    current_responsible_user_id = fields.Many2one('res.users', compute='_compute_current_approval', store=True)
    workflow_id = fields.Many2one('qaqc.prq.workflow', readonly=True, copy=False, tracking=True)
    approval_ids = fields.One2many('qaqc.prq.approval', 'prq_id', string='Approval History', copy=False)
    approval_count = fields.Integer(compute='_compute_approval_count')
    approved_by_id = fields.Many2one('res.users', readonly=True, copy=False, tracking=True)
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    consultant_rep_id = fields.Many2one('res.partner', string='Consultant Representative')
    consultant_comments = fields.Text(string='Final / Consultant Comments', tracking=True)
    rejection_reason = fields.Text(tracking=True)
    company_profile = fields.Binary(string='Company Profile', attachment=True)
    company_profile_fname = fields.Char(string='Filename')
    financial_statement = fields.Binary(string='Financial Statement', attachment=True)
    financial_statement_fname = fields.Char(string='Filename')
    previous_projects = fields.Binary(string='Previous Projects List', attachment=True)
    previous_projects_fname = fields.Char(string='Filename')
    iso_certificates = fields.Binary(string='ISO / Quality Certificates', attachment=True)
    iso_certificates_fname = fields.Char(string='Filename')
    other_attachments = fields.Many2many('ir.attachment', 'qaqc_prq_ir_attachment_rel', 'prq_id', 'attachment_id', string='Other Supporting Files')
    document_ids = fields.Many2many('documents.document', compute='_compute_documents', string='Documents files')
    document_count = fields.Integer(compute='_compute_documents')
    active = fields.Boolean(default=True)

    @api.depends('approval_ids.state', 'approval_ids.assigned_user_id', 'approval_ids.run_number', 'approval_ids.sequence')
    def _compute_current_approval(self):
        for rec in self:
            latest_run = max(rec.approval_ids.mapped('run_number') or [0])
            pending = rec.approval_ids.filtered(lambda a: a.run_number == latest_run and a.state == 'pending').sorted(lambda a: (a.sequence, a.id))
            rec.current_approval_id = pending[:1]
            rec.current_responsible_user_id = pending[:1].assigned_user_id if pending else False

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.approval_ids)

    def _compute_documents(self):
        Document = self.env['documents.document']
        for rec in self:
            docs = Document.search([('res_model', '=', rec._name), ('res_id', '=', rec.id)])
            rec.document_ids = docs
            rec.document_count = len(docs)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('qaqc.prq') or 'PRQ/New'
        return super().create(vals_list)

    def _is_manager(self):
        return self.env.user.has_group('qaqc_prq_odoo19.group_qaqc_manager') or self.env.user.has_group('base.group_system')

    def _check_editable(self):
        for rec in self:
            if rec.state not in ('draft', 'revise_resubmit') and not self._is_manager():
                raise UserError(_('Only draft or returned PRQ requests can be edited. A manager may perform controlled corrections.'))

    def write(self, vals):
        protected = {'state','workflow_id','approved_by_id','approval_date','revision'}
        if protected.intersection(vals) and not self.env.context.get('qaqc_workflow_action') and not self._is_manager():
            raise AccessError(_('Workflow fields can only be changed through the workflow actions.'))
        business_fields = {'project_id','supplier_id','discipline','scope_description','date','company_profile','financial_statement','previous_projects','iso_certificates','other_attachments'}
        if business_fields.intersection(vals):
            self._check_editable()
        return super().write(vals)

    def _get_workflow(self):
        self.ensure_one()
        Workflow = self.env['qaqc.prq.workflow'].sudo()
        domain = [('active','=',True), ('company_id','in',[self.env.company.id, False])]
        specific = Workflow.search(domain + [('project_id','=',self.project_id.id)], limit=1)
        general = Workflow.search(domain + [('project_id','=',False)], limit=1)
        workflow = specific or general
        if not workflow or not workflow.step_ids:
            raise UserError(_('No active PRQ approval workflow is configured for this project. Ask a QA/QC manager to configure it first.'))
        return workflow

    def _check_step_access(self, approval):
        self.ensure_one()
        if self._is_manager():
            return True
        user = self.env.user
        if approval.assigned_user_id:
            allowed = approval.assigned_user_id == user
        elif approval.assigned_group_id:
            allowed = approval.assigned_group_id in user.groups_id
        else:
            allowed = False
        if not allowed:
            raise AccessError(_('You are not assigned to the current PRQ approval step.'))
        return True

    def _create_document_record(self, attachment, label):
        """Link existing uploaded supporting attachments into Documents where possible."""
        self.ensure_one()
        if not attachment:
            return
        folder = self.env['documents.document'].sudo().search([('name', '=', 'QA/QC PRQ')], limit=1)
        # Avoid creating a Documents record without a configured folder; user can still access attachment in chatter/form.
        if not folder:
            return
        self.env['documents.document'].sudo().create({
            'name': '%s - %s' % (self.name, label),
            'folder_id': folder.id,
            'attachment_id': attachment.id,
            'owner_id': self.prepared_by_id.id,
            'partner_id': self.supplier_id.id,
            'res_model': self._name,
            'res_id': self.id,
        })

    def action_submit(self):
        for rec in self:
            if rec.state not in ('draft','revise_resubmit'):
                raise UserError(_('Only draft or returned PRQ requests can be submitted.'))
            if not (rec.company_profile or rec.financial_statement or rec.previous_projects or rec.iso_certificates or rec.other_attachments):
                raise UserError(_('Attach at least one supporting document before submission.'))
            workflow = rec._get_workflow()
            steps = workflow.step_ids.sorted(lambda s: (s.sequence, s.id))
            if not steps:
                raise UserError(_('The selected workflow has no approval steps.'))
            rec.with_context(qaqc_workflow_action=True).write({'state':'submitted','workflow_id':workflow.id,'rejection_reason':False})
            run_number = max(rec.approval_ids.mapped('run_number') or [0]) + 1
            for step in steps:
                rec.env['qaqc.prq.approval'].sudo().create({
                    'prq_id':rec.id, 'run_number':run_number, 'sequence':step.sequence, 'step_name':step.name,
                    'role':step.role, 'assigned_user_id':step.user_id.id,
                    'assigned_group_id':step.group_id.id, 'state':'pending' if step.required else 'skipped',
                })
            rec.message_post(body=_('PRQ submitted. Approval workflow: %s') % workflow.name)
            rec._notify_current_approver()
            rec._advance_if_skipped()
        return True

    def _notify_current_approver(self):
        self.ensure_one()
        approval = self.current_approval_id
        if not approval:
            return
        users = approval.assigned_user_id
        if not users and approval.assigned_group_id:
            users = approval.assigned_group_id.users
        for user in users:
            self.activity_schedule('mail.mail_activity_data_todo', user_id=user.id,
                summary=_('PRQ approval required: %s') % self.name,
                note=_('Please review the supplier pre-qualification request and record your decision.'))

    def _advance_if_skipped(self):
        for rec in self:
            if rec.state in ('submitted','under_review') and not rec.current_approval_id:
                rec._finalize_approval()
            elif rec.state == 'submitted' and rec.current_approval_id:
                rec.with_context(qaqc_workflow_action=True).write({'state':'under_review'})

    def action_start_review(self):
        for rec in self:
            approval = rec.current_approval_id
            if rec.state != 'submitted' or not approval:
                raise UserError(_('There is no submitted PRQ awaiting review.'))
            rec._check_step_access(approval)
            rec.with_context(qaqc_workflow_action=True).write({'state':'under_review'})
        return True

    def _complete_current(self, decision, comments=False):
        self.ensure_one()
        approval = self.current_approval_id
        if not approval:
            raise UserError(_('No pending approval step was found.'))
        self._check_step_access(approval)
        approval.with_context(qaqc_approval_action=True).write({'state':'approved' if decision == 'approve' else ('returned' if decision == 'return' else 'rejected'),
            'decision':decision, 'comments':comments or False,
            'decision_by_id':self.env.user.id, 'decision_date':fields.Datetime.now()})
        self.message_post(body=_('Approval step "%s": %s') % (approval.step_name, dict(approval._fields['decision'].selection).get(decision, decision)) + (('<br/>%s' % comments) if comments else ''))
        if decision == 'reject':
            self.with_context(qaqc_workflow_action=True).write({'state':'rejected','rejection_reason':comments or _('Rejected')})
            return
        if decision == 'return':
            self.with_context(qaqc_workflow_action=True).write({'state':'revise_resubmit','revision':self.revision + 1})
            return
        latest_run = max(self.approval_ids.mapped('run_number') or [0])
        next_pending = self.approval_ids.filtered(lambda a: a.run_number == latest_run and a.state == 'pending').sorted(lambda a: (a.sequence,a.id))
        if next_pending:
            self.with_context(qaqc_workflow_action=True).write({'state':'under_review'})
            self._notify_current_approver()
            self._advance_if_skipped()
        else:
            self._finalize_approval()

    def action_approve_step(self):
        for rec in self:
            rec._complete_current('approve', rec.env.context.get('approval_comments'))
        return True

    def action_return_for_changes(self):
        for rec in self:
            comments = rec.env.context.get('approval_comments') or rec.consultant_comments
            if not comments:
                raise UserError(_('Enter comments explaining what must be corrected before returning the request.'))
            rec._complete_current('return', comments)
        return True

    def action_reject(self):
        for rec in self:
            comments = rec.env.context.get('approval_comments') or rec.rejection_reason
            if not comments:
                raise UserError(_('Enter a rejection reason before rejecting the request.'))
            rec._complete_current('reject', comments)
        return True

    def _finalize_approval(self):
        for rec in self:
            rec.with_context(qaqc_workflow_action=True).write({'state':'approved','approved_by_id':self.env.user.id,'approval_date':fields.Datetime.now()})
            # General partner flag for compatibility; project-specific approvals remain recorded on this PRQ.
            rec.supplier_id.sudo().write({'qaqc_approved_vendor':True})
            rec.message_post(body=_('PRQ approved. Supplier qualification completed for project %s.') % rec.project_id.display_name)
            rec._create_documents_for_attachments()

    def _create_documents_for_attachments(self):
        self.ensure_one()
        Document = self.env['documents.document'].sudo()
        folder = Document.search([('name','=','QA/QC PRQ')], limit=1)
        if not folder:
            return
        attachment_ids = []
        for field_name in ('company_profile','financial_statement','previous_projects','iso_certificates'):
            value = self[field_name]
            if value:
                attachment = self.env['ir.attachment'].sudo().search([('res_model','=','qaqc.prq'),('res_id','=',self.id),('res_field','=',field_name)], limit=1)
                if attachment:
                    attachment_ids.append((attachment, field_name.replace('_',' ').title()))
        attachment_ids += [(a, a.name or 'Attachment') for a in self.other_attachments]
        for attachment, label in attachment_ids:
            exists = Document.search([('res_model','=','qaqc.prq'),('res_id','=',self.id),('attachment_id','=',attachment.id)], limit=1)
            if not exists:
                self._create_document_record(attachment, label)

    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft','rejected','revise_resubmit') and not rec._is_manager():
                raise UserError(_('Only draft, rejected, or returned requests can be cancelled by a non-manager.'))
            rec.with_context(qaqc_workflow_action=True).write({'state':'cancelled'})
            rec.message_post(body=_('PRQ cancelled by %s.') % self.env.user.display_name)
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if not rec._is_manager():
                raise AccessError(_('Only a QA/QC manager can reset a PRQ to draft.'))
            if rec.state not in ('rejected','cancelled','revise_resubmit'):
                raise UserError(_('Only rejected, cancelled, or returned PRQs can be reset.'))
            rec.with_context(qaqc_workflow_action=True).write({'state':'draft','revision':rec.revision + 1})
        return True
