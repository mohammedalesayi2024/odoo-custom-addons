# -*- coding: utf-8 -*-
{
    'name': 'QA/QC Documents - PRQ Workflow',
    'version': '19.0.1.0.0',
    'category': 'Operations/Project',
    'summary': 'Configurable supplier pre-qualification workflow inside Odoo Documents',
    'description': """
QA/QC PRQ Workflow for Odoo 19
==============================
Adds a configurable Pre-Qualification Request (PRQ) approval workflow,
project-specific approval routing, decision history, supplier approval status,
and attachment handling. The menus are integrated into the Documents application.
    """,
    'author': 'Custom implementation',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'contacts', 'project', 'documents'],
    'data': [
        'security/qaqc_security.xml',
        'security/ir.model.access.csv',
        'data/qaqc_sequences.xml',
        'views/qaqc_workflow_views.xml',
        'views/qaqc_prq_views.xml',
        'views/project_views.xml',
        'views/qaqc_menus.xml',
    ],
    'installable': True,
    'application': False,
}
