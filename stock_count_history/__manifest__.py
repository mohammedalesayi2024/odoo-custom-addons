{
    'name': 'Stock Count History',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Keep a permanent read-only snapshot of every inventory count applied',
    'description': """
Saves a snapshot (theoretical qty, counted qty, difference, user, date) of every
quant adjusted when "Apply" is pressed in Inventory > Physical Inventory,
and exposes it in Inventory > Reporting > Inventory Count History.
    """,
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/stock_count_history_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
