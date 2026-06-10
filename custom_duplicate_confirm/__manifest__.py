{
    'name': 'Confirm Duplicate Product',
    'version': '1.0',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'custom_duplicate_confirm/static/src/js/confirm_duplicate.js',
        ],
    },
    'installable': True,
}