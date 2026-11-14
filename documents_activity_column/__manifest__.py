{
    'name': 'Documents Activity Column',
    'version': '19.0.1.2.0',
    'category': 'Productivity/Documents',
    'summary': 'Add the Activities column to the Documents list view',
    'author': 'Mohammed Alesayi',
    'depends': ['documents', 'mail'],
    'data': [
        'security/mail_activity_security.xml',
        'views/res_users_activity_permissions.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
