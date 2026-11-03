# -*- coding: utf-8 -*-
from odoo import fields, models
class ProjectProject(models.Model):
    _inherit='project.project'
    project_code=fields.Char(string='Project Code'); contractor_code=fields.Char(string='Contractor Code'); project_no=fields.Char(string='Project No.')
    employer_id=fields.Many2one('res.partner',string='Employer'); engineer_id=fields.Many2one('res.partner',string='Engineer / Consultant'); contractor_id=fields.Many2one('res.partner',string='Contractor')
    qaqc_prq_ids=fields.One2many('qaqc.prq','project_id'); qaqc_mar_ids=fields.One2many('qaqc.mar','project_id')
