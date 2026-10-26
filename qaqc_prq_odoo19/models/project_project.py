from odoo import fields, models

class ProjectProject(models.Model):
    _inherit = 'project.project'

    qaqc_project_code = fields.Char(string='QA/QC Project Code')
    qaqc_contractor_code = fields.Char(string='QA/QC Contractor Code', default='TH')
    qaqc_employer_id = fields.Many2one('res.partner', string='Employer')
    qaqc_engineer_id = fields.Many2one('res.partner', string='Consultant / Engineer')
    qaqc_contractor_id = fields.Many2one('res.partner', string='Contractor')
    qaqc_prq_ids = fields.One2many('qaqc.prq', 'project_id', string='PRQ Requests')
    qaqc_prq_count = fields.Integer(compute='_compute_qaqc_prq_count')

    def _compute_qaqc_prq_count(self):
        for rec in self:
            rec.qaqc_prq_count = len(rec.qaqc_prq_ids)

    def action_view_qaqc_prq(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': 'PRQ Requests',
            'res_model': 'qaqc.prq', 'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
