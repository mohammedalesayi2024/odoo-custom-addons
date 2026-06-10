{
    'name': 'Fabric Discount POS',
    'version': '1.0',
    'depends': ['point_of_sale', 'barcodes'],
    'data': [
        'data/barcode_rule.xml',
    ],
    'assets': {
        'point_of_sale.assets': [  # ✅ التصحيح هنا
            'fabric_discount_pos/static/src/js/barcode_price_qty.js',
        ],
    },
    'installable': True,
}