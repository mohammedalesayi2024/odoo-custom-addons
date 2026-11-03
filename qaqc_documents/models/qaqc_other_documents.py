# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

class QaqcMes(models.Model):
    _name='qaqc.mes'; _description='Method Statement (MES)'; _inherit=['qaqc.document.mixin']; _doc_type_code='MES'; _sequence_code='qaqc.mes'
    attachment_ids=fields.Many2many('ir.attachment','qaqc_mes_attachment_rel','document_id','attachment_id',string='Attachments',copy=False)
    title=fields.Char(required=True); purpose_scope=fields.Text(); references=fields.Text(); sequence_of_work=fields.Text(); risks_controls=fields.Text(); emergency_arrangements=fields.Text(); supervision=fields.Text(); housekeeping=fields.Text()
    method_statement_attachment_ids=fields.Many2many('ir.attachment', 'qaqc_mes_method_attachment_rel', 'mes_id','attachment_id',string='Method Statement Files')
    itp_line_ids=fields.One2many('qaqc.mes.itp.line','mes_id'); icl_line_ids=fields.One2many('qaqc.mes.icl.line','mes_id'); risk_line_ids=fields.One2many('qaqc.mes.risk.line','mes_id')
class QaqcMesIptLine(models.Model):
    _name='qaqc.mes.itp.line'; _description='MES ITP Activity'; _order='sequence,id'
    mes_id=fields.Many2one('qaqc.mes',required=True,ondelete='cascade'); sequence=fields.Integer(default=10); activity=fields.Char(required=True); inspection_criteria=fields.Char(); reference=fields.Char(); frequency=fields.Char(); code=fields.Selection([('H','Hold'),('R','Review'),('A','Approve'),('S','Surveillance'),('I','Inspect')])
class QaqcMesIclLine(models.Model):
    _name='qaqc.mes.icl.line'; _description='MES Inspection Checklist'
    mes_id=fields.Many2one('qaqc.mes',required=True,ondelete='cascade'); item=fields.Char(required=True); result=fields.Selection([('yes','Yes'),('no','No'),('na','N/A')]); engineer_note=fields.Char()
class QaqcMesRiskLine(models.Model):
    _name='qaqc.mes.risk.line'; _description='MES Risk Assessment'
    mes_id=fields.Many2one('qaqc.mes',required=True,ondelete='cascade'); hazard=fields.Char(required=True); consequence=fields.Char(); control_measure=fields.Text(); responsible=fields.Char()

class QaqcMir(models.Model):
    _name='qaqc.mir'; _description='Material Inspection Request (MIR)'; _inherit=['qaqc.document.mixin']; _doc_type_code='MIR'; _sequence_code='qaqc.mir'
    attachment_ids=fields.Many2many('ir.attachment','qaqc_mir_attachment_rel','document_id','attachment_id',string='Attachments',copy=False)
    mar_id=fields.Many2one('qaqc.mar',required=True,domain="[('state','in',('approved','approved_noted'))]"); material_description=fields.Text(required=True); quantity=fields.Float(); uom=fields.Char(); manufacturer=fields.Char(); model_no=fields.Char(); serial_no=fields.Char(); country_of_origin=fields.Char(); arrival_date=fields.Date(); storage_location=fields.Char(); delivery_note=fields.Char()
    physical_damage=fields.Boolean(); inspection_details=fields.Text(); accessories_included=fields.Boolean(); conforms_to_approved_submission=fields.Boolean()
    @api.constrains('mar_id')
    def _check_approved_mar(self):
        for rec in self:
            if rec.mar_id and rec.mar_id.state not in ('approved','approved_noted'):
                raise ValidationError('MIR can only be linked to a MAR with Consultant decision A or B.')

class QaqcRsn(models.Model):
    _name='qaqc.rsn'; _description='Request Start New (RSN)'; _inherit=['qaqc.document.mixin']; _doc_type_code='RSN'; _sequence_code='qaqc.rsn'
    attachment_ids=fields.Many2many('ir.attachment','qaqc_rsn_attachment_rel','document_id','attachment_id',string='Attachments',copy=False)
    work_description=fields.Text(required=True); planned_date=fields.Date(); inspection_time=fields.Char(); floor=fields.Char(); area=fields.Char(); zone=fields.Char(); approval_documents_ref=fields.Char(); mar_id=fields.Many2one('qaqc.mar'); mes_id=fields.Many2one('qaqc.mes'); notice_hours=fields.Integer(default=24)
    discipline_approval_ids=fields.One2many('qaqc.rsn.discipline.approval','rsn_id')
class QaqcRsnDisciplineApproval(models.Model):
    _name='qaqc.rsn.discipline.approval'; _description='RSN Discipline Approval'
    rsn_id=fields.Many2one('qaqc.rsn',required=True,ondelete='cascade'); discipline=fields.Selection([('civil','Civil'),('arch','Architecture'),('mech','Mechanical'),('elec','Electrical')],required=True); inspector_name=fields.Char(); clear_to_proceed=fields.Boolean(); comments=fields.Char()

class QaqcWir(models.Model):
    _name='qaqc.wir'; _description='Work Inspection Request (WIR)'; _inherit=['qaqc.document.mixin']; _doc_type_code='WIR'; _sequence_code='qaqc.wir'
    attachment_ids=fields.Many2many('ir.attachment','qaqc_wir_attachment_rel','document_id','attachment_id',string='Attachments',copy=False)
    inspection_description=fields.Text(required=True); inspection_date=fields.Date(); inspection_time=fields.Char(); floor=fields.Char(); area=fields.Char(); zone=fields.Char(); shop_drawing_ref=fields.Char(); rsn_id=fields.Many2one('qaqc.rsn'); internal_qa_qc_passed=fields.Boolean(default=False); commercial_notified=fields.Boolean(readonly=True,copy=False)
    def action_qaqc_approve(self):
        result=super().action_qaqc_approve()
        self.with_context(qaqc_workflow=True).write({'internal_qa_qc_passed':True})
        return result
    def _consultant_decide(self, decision):
        result=super()._consultant_decide(decision)
        if decision in ('A','B'):
            self.with_context(qaqc_workflow=True).write({'commercial_notified':True})
            for rec in self: rec.activity_schedule('mail.mail_activity_data_todo',user_id=rec._get_group_user('group_qaqc_commercial'),summary='WIR approved - commercial action',note='Prepare the relevant payment certificate process.')
        return result

class QaqcNcr(models.Model):
    _name='qaqc.ncr'; _description='Non-Conformance Report (NCR)'; _inherit=['qaqc.document.mixin']; _doc_type_code='NCR'; _sequence_code='qaqc.ncr'
    attachment_ids=fields.Many2many('ir.attachment','qaqc_ncr_attachment_rel','document_id','attachment_id',string='Attachments',copy=False)
    source_wir_id=fields.Many2one('qaqc.wir',string='Related WIR (Optional)'); issue_description=fields.Text(required=True); discovery_date=fields.Date(default=fields.Date.context_today); deadline=fields.Date(); corrective_action=fields.Text(); preventive_action=fields.Text(); closure_comments=fields.Text()
    ncr_state=fields.Selection([('open','Open'),('in_progress','In Progress'),('closed','Closed')],default='open',tracking=True)
    def action_start_corrective_action(self): self.with_context(qaqc_workflow=True).write({'ncr_state':'in_progress'})
    def action_close_ncr(self):
        if not self.env.user.has_group('qaqc_documents.group_qaqc_engineer') and not self.env.user.has_group('qaqc_documents.group_qaqc_manager'):
            raise UserError('Only QA/QC can close an NCR.')
        for rec in self:
            if not rec.corrective_action: raise UserError('Enter the corrective action before closing the NCR.')
            rec.with_context(qaqc_workflow=True).write({'ncr_state':'closed','state':'closed'})
            rec.message_post(body='NCR closed. ' + (rec.closure_comments or ''))
