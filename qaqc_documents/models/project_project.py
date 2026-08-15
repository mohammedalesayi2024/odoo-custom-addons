# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectProject(models.Model):
    """Extends project.project with the fixed header information that
    appears on every single QA/QC document (Employer / Engineer /
    Contractor letterhead block seen in all the real templates)."""
    _inherit = 'project.project'

    project_code = fields.Char(
        string='Project Code',
        help="Short project code used in document references, e.g. 'JRP' "
             "for 'TH-JRP-MAR-CIV-0000'.")
    contractor_code = fields.Char(
        string='Contractor Code',
        help="Short contractor code used as the document reference prefix, "
             "e.g. 'TH' for Tatweer Holding.")
    project_no = fields.Char(string='Project No.', help="e.g. P632")

    employer_id = fields.Many2one('res.partner', string='Employer')
    engineer_id = fields.Many2one('res.partner', string='Engineer (Consultant)')
    contractor_id = fields.Many2one('res.partner', string='Contractor')

    qaqc_prq_ids = fields.One2many('qaqc.prq', 'project_id', string='PRQ Documents')
    qaqc_prq_count = fields.Integer(compute='_compute_qaqc_prq_count')

    def _compute_qaqc_prq_count(self):
        for project in self:
            project.qaqc_prq_count = len(project.qaqc_prq_ids)

    def action_view_qaqc_prq(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'PRQ Documents',
            'res_model': 'qaqc.prq',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
