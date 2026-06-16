{
    'name': 'Advance Audit',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Advanced Audit Trail',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',

        'views/audit_event_views.xml',
        'views/audit_actions.xml',
        'views/audit_menus.xml',
    ],
    'installable': True,
    'application': True,
}