{
    'name': 'صيانة الوحدات',
    'summary': 'صيانة الوحدات السكنية (ضمان داخلي وخارجي) مع تطبيق الفني وشكاوى العملاء عبر OTP',
    'description': """
صيانة الوحدات
=============
* المباني والوحدات وملاك الوحدات (عملاء Odoo) وفترة الضمان.
* طلبات صيانة داخلية وخارجية بترقيم متسلسل.
* مسار الفني: المنتجات، تسعير الإدارة، توقيع العميل، بدء الصيانة بالمؤقت، الصور قبل وبعد، التقرير.
* تقرير PDF يُرسل للعميل بالبريد أو واتساب، مع إعادة الإرسال في أي وقت.
* شكاوى العملاء من التطبيق بدون تسجيل دخول عبر رمز تحقق OTP يرسله Odoo.
* واجهة API لتطبيق الجوال.
""",
    'version': '19.0.1.0.2',
    'category': 'Services',
    'author': 'Unit Maintenance',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'product', 'account', 'stock', 'sms'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/sequence_data.xml',
        'data/config_data.xml',
        'report/request_report.xml',
        'views/building_views.xml',
        'views/unit_views.xml',
        'views/request_views.xml',
        'views/complaint_views.xml',
        'views/menu.xml',
    ],
    'application': True,
    'installable': True,
}
