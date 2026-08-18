{
    'name': 'Custom Audit Log',
    'version': '19.0.1.0.0',
    'summary': 'تتبع عمليات الإضافة والتعديل والحذف لكل مستخدم مع القيم قبل وبعد التعديل',
    'description': """
Custom Audit Log
=================
موديول تدقيق مخصص يقوم بـ:
- تسجيل كل عملية إضافة (Create) / تعديل (Write) / حذف (Unlink) تلقائيًا
- حفظ القيمة قبل وبعد التعديل لكل حقل تم تغييره
- إمكانية الفلترة حسب التاريخ، مستخدم واحد أو عدة مستخدمين، الموديل، ونوع العملية
- التحكم بالموديلات المتتبَّعة عبر قائمة بيضاء (Whitelist) من واجهة الإعدادات
""",
    'category': 'Tools',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/audit_log_views.xml',
        'views/audit_config_views.xml',
    ],
    'installable': True,
    'application': False,
}
