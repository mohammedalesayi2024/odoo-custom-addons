# -*- coding: utf-8 -*-
{
    'name': 'QA/QC Documents',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'QA/QC document workflow: PRQ, MAR, MES, MIR, RSN, WIR, NCR',
    'description': """
QA/QC Documents Management
===========================
Manages the full quality assurance / quality control document lifecycle
for construction projects:

* PRQ  - Pre-Qualification
* MAR  - Material Approval Request
* MES  - Method of Statement (Method Statement + ITP + ICL + Risk Assessment)
* MIR  - Material Inspection Request
* RSN  - Request Start New (activity)
* WIR  - Work Inspection Request
* NCR  - Non-Conformance Report

Built from the actual company workflow chart and real project document
templates (Jeddah Rose Project).
    """,
    'author': 'Your Company',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'project',
    ],
    'data': [
        # security
        'security/qaqc_security_groups.xml',
        'security/ir.model.access.csv',
        'security/qaqc_record_rules.xml',
        # data
        'data/qaqc_sequences.xml',
        # views
        'views/project_project_views.xml',
        'views/qaqc_prq_views.xml',
        'views/qaqc_mar_views.xml',
        'views/qaqc_menus.xml',
    ],
    'installable': True,
    'application': True,
}
