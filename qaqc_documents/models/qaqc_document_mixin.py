# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class QaqcDocumentMixin(models.AbstractModel):
    _name = 'qaqc.document.mixin'
    _description = 'QA/QC Document Common Fields'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    _doc_type_code = 'DOC'
    _sequence_code = False

    name = fields.Char(string='Document Ref.', default='New', readonly=True, copy=False, tracking=True)
    project_id = fields.Many2one('project.project', required=True, tracking=True, index=True)
    discipline = fields.Selection([('civil','Civil'),('arch','Architecture'),('mech','Mechanical'),('elec','Electrical'),('id','ID'),('ffe','FFE'),('other','Other')], required=True, default='civil', tracking=True)
    rev = fields.Integer(string='Revision', default=0, readonly=True, copy=False, tracking=True)
    date = fields.Date(default=fields.Date.context_today, tracking=True)
    state = fields.Selection([
        ('draft','Draft'), ('qa_review','Pending QA/QC'), ('consultant_review','Pending Consultant'),
        ('approved','A - Approved'), ('approved_noted','B - Approved as Noted'),
        ('revise_resubmit','C - Revise & Resubmit'), ('rejected','D - Rejected'), ('closed','Closed')
    ], default='draft', required=True, copy=False, tracking=True, index=True)
    prepared_by_id = fields.Many2one('res.users', default=lambda self:self.env.user, readonly=True, tracking=True)
    qaqc_reviewer_id = fields.Many2one('res.users', string='QA/QC Reviewer', readonly=True, copy=False, tracking=True)
    qa_qc_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    qa_qc_comments = fields.Text(string='QA/QC Review Comments', tracking=True)
    consultant_rep_id = fields.Many2one('res.partner', string="Consultant's Representative", tracking=True)
    consultant_decision = fields.Selection([('A','A - Approved'),('B','B - Approved as Noted'),('C','C - Revise and Resubmit'),('D','D - Rejected')], copy=False, tracking=True)
    consultant_comments = fields.Text(string="Consultant's Comments", tracking=True)
    consultant_user_id = fields.Many2one('res.users', string='Consultant User', readonly=True, copy=False)
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', copy=False)
    revision_ids = fields.Many2many('qaqc.document.revision', compute='_compute_revision_ids', string='Revision History')
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                project = self.env['project.project'].browse(vals.get('project_id'))
                discipline = vals.get('discipline', 'civil')
                disc = {'civil':'CIV','arch':'ARC','mech':'MEC','elec':'ELE','id':'ID','ffe':'FFE','other':'OTH'}.get(discipline, 'CIV')
                contractor_code = (project.contractor_code or 'TH').strip().upper()
                project_code = (project.project_code or (project.name or 'PRJ')[:3]).strip().upper()
                prefix = '%s-%s-%s-%s-' % (contractor_code, project_code, self._doc_type_code, disc)
                # Keep a separate sequence for every project + document type + discipline.
                sequence_code = 'qaqc.%s.%s.%s.%s' % (self._name.replace('.', '_'), project.id, self._doc_type_code.lower(), disc.lower())
                sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], order='id', limit=1)
                if not sequence:
                    existing_names = self.search([('name', '=like', prefix + '%')]).mapped('name')
                    used_numbers = []
                    for existing_name in existing_names:
                        suffix = existing_name.rsplit('-', 1)[-1]
                        if suffix.isdigit():
                            used_numbers.append(int(suffix))
                    sequence = self.env['ir.sequence'].create({
                        'name': 'QA/QC %s - Project %s - %s' % (self._doc_type_code, project.display_name, disc),
                        'code': sequence_code,
                        'implementation': 'standard',
                        'padding': 4,
                        'number_next': max(used_numbers or [0]) + 1,
                        'company_id': False,
                    })
                seq = sequence.next_by_id()
                vals['name'] = '%s%s' % (prefix, seq)
        records = super().create(vals_list)
        for rec in records:
            rec.message_subscribe(partner_ids=[rec.prepared_by_id.partner_id.id])
            rec._post_new_attachments(rec.attachment_ids.ids)
            rec._post_binary_field_attachments()
        return records

    def _compute_revision_ids(self):
        for rec in self:
            rec.revision_ids = self.env['qaqc.document.revision'].search([('document_model','=',rec._name),('document_res_id','=',rec.id)], order='revision desc')

    def write(self, vals):
        if 'state' in vals and not self.env.context.get('qaqc_workflow'):
            raise UserError('Document status can only be changed using the workflow buttons.')
        protected = set(vals) - {'consultant_comments', 'attachment_ids'}
        for rec in self:
            if rec.state not in ('draft','revise_resubmit') and protected and not self.env.context.get('qaqc_workflow'):
                raise UserError('Document details are locked after submission. Use the Revise & Resubmit cycle to edit them.')
        old_attachments = {r.id:set(r.attachment_ids.ids) for r in self} if 'attachment_ids' in vals else {}
        result = super().write(vals)
        if 'attachment_ids' in vals:
            for rec in self:
                added = set(rec.attachment_ids.ids) - old_attachments.get(rec.id,set())
                rec._post_new_attachments(list(added))
        if any(name in self._fields and self._fields[name].type == 'binary' for name in vals):
            for rec in self: rec._post_binary_field_attachments()
        return result

    def _post_binary_field_attachments(self):
        attachments = self.env['ir.attachment'].search([('res_model','=',self._name),('res_id','=',self.id),('res_field','!=',False)])
        if attachments:
            self.message_post(body='Document file(s) uploaded or updated.', attachment_ids=attachments.ids, subtype_xmlid='mail.mt_note')

    def _post_new_attachments(self, attachment_ids):
        if attachment_ids:
            attachments = self.env['ir.attachment'].browse(attachment_ids).exists()
            attachments.write({'res_model': self._name, 'res_id': self.id})
            self.message_post(body='New document attachment(s) uploaded.', attachment_ids=attachments.ids, subtype_xmlid='mail.mt_note')

    def _subscribe_group(self, group_xmlid):
        group = self.env.ref('qaqc_documents.' + group_xmlid, raise_if_not_found=False)
        if group:
            # In Odoo 19, group membership is exposed by res.groups.user_ids.
            users = group.sudo().user_ids.filtered(
                lambda user: user.active and not user.share
            )
            partners = users.mapped('partner_id')
            if partners:
                self.message_subscribe(partner_ids=partners.ids)

    def _require_group(self, xmlid, message):
        if not self.env.user.has_group(xmlid):
            raise UserError(message)

    def action_submit(self):
        for rec in self:
            if rec.state not in ('draft','revise_resubmit'):
                raise UserError('Only Draft or Revise & Resubmit documents can be submitted.')
            rec.with_context(qaqc_workflow=True).write({'state':'qa_review','qa_qc_date':False,'qaqc_reviewer_id':False,'consultant_decision':False,'consultant_comments':False,'approval_date':False})
            rec._subscribe_group('group_qaqc_engineer')
            rec.message_post(body='Document submitted for internal QA/QC review.')
            rec.activity_schedule('mail.mail_activity_data_todo', user_id=rec._get_group_user('group_qaqc_engineer'), summary='QA/QC review required', note='Review submitted document and approve or reject it.')

    def _get_group_user(self, group_xmlid):
        group = self.env.ref('qaqc_documents.' + group_xmlid, raise_if_not_found=False)
        if not group:
            return self.env.user.id
        users = group.sudo().user_ids.filtered(
            lambda user: user.active and not user.share
        )
        return users[:1].id or self.env.user.id

    def action_qaqc_approve(self):
        self._require_group('qaqc_documents.group_qaqc_engineer','Only QA/QC team members can perform the internal review.')
        for rec in self:
            if rec.state != 'qa_review': raise UserError('This document is not waiting for QA/QC review.')
            rec.with_context(qaqc_workflow=True).write({'state':'consultant_review','qaqc_reviewer_id':self.env.user.id,'qa_qc_date':fields.Datetime.now()})
            rec._subscribe_group('group_qaqc_consultant')
            rec.message_post(body='QA/QC internal review approved. Document forwarded directly to the Consultant.')
            rec.activity_schedule('mail.mail_activity_data_todo', user_id=rec._get_group_user('group_qaqc_consultant'), summary='Consultant decision required', note='Select decision A, B, C or D and enter comments.')

    def action_qaqc_reject(self):
        self._require_group('qaqc_documents.group_qaqc_engineer','Only QA/QC team members can reject at the internal review stage.')
        for rec in self:
            if rec.state != 'qa_review': raise UserError('This document is not waiting for QA/QC review.')
            if not rec.qa_qc_comments: raise UserError('Enter QA/QC rejection comments before rejecting the document.')
            rec.with_context(qaqc_workflow=True).write({'state':'rejected','qaqc_reviewer_id':self.env.user.id,'qa_qc_date':fields.Datetime.now()})
            rec.message_post(body='Document rejected by QA/QC. It has not been forwarded to the Consultant. ' + (rec.qa_qc_comments or ''))

    def _consultant_decide(self, decision):
        self._require_group('qaqc_documents.group_qaqc_consultant','Only Consultant users can make the final A/B/C/D decision.')
        for rec in self:
            if rec.state != 'consultant_review': raise UserError('Only documents approved by QA/QC can receive a Consultant decision.')
            if decision not in ('A','B','C','D'): raise ValidationError('Invalid Consultant decision.')
            if decision in ('B','C','D') and not rec.consultant_comments:
                raise UserError('Please enter Consultant comments for decisions B, C and D.')
            state = {'A':'approved','B':'approved_noted','C':'revise_resubmit','D':'rejected'}[decision]
            if decision == 'C':
                self.env['qaqc.document.revision'].create({'document_model':rec._name,'document_res_id':rec.id,'revision':rec.rev,'decision':'C - Revise & Resubmit','comments':rec.consultant_comments,'attachment_ids':[(6,0,rec.attachment_ids.ids)]})
            vals = {'state':state,'consultant_decision':decision,'consultant_user_id':self.env.user.id,'approval_date':fields.Datetime.now()}
            if decision == 'C': vals['rev'] = rec.rev + 1
            rec.with_context(qaqc_workflow=True).write(vals)
            rec.message_post(body='Consultant decision: %s. %s' % (decision, rec.consultant_comments or ''))

    def action_consultant_approve(self): self._consultant_decide('A')
    def action_consultant_approve_noted(self): self._consultant_decide('B')
    def action_consultant_revise(self): self._consultant_decide('C')
    def action_consultant_reject(self): self._consultant_decide('D')

    def action_reset_to_draft(self):
        self._require_group('qaqc_documents.group_qaqc_manager','Only QA/QC Managers can reset a document.')
        for rec in self:
            rec.with_context(qaqc_workflow=True).write({'state':'draft','consultant_decision':False})


class QaqcDocumentRevision(models.Model):
    _name = 'qaqc.document.revision'
    _description = 'QA/QC Document Revision Log'
    _order = 'create_date desc'
    document_model = fields.Char(required=True, index=True)
    document_res_id = fields.Integer(required=True, index=True)
    revision = fields.Integer(required=True)
    decision = fields.Char()
    comments = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string='Revision Attachments')
    changed_by = fields.Many2one('res.users', default=lambda self:self.env.user, readonly=True)
    changed_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
