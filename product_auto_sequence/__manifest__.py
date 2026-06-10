{
    'name': 'Product Auto Sequence',
    'version': '1.0',
    'depends': ['product'],
    'data': [
         'security/ir.model.access.csv',  # 👈 مهم جدًا
         'data/sequence.xml',
         'views/product_views.xml',  # 👈 أضف هذا

    ],
    'installable': True,
    'application': False,
}