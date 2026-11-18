from odoo import http
from odoo.http import request
from odoo.modules.module import get_module_resource


class TechnicianApp(http.Controller):

    @http.route('/unit_maintenance/app', type='http', auth='public', methods=['GET'],
                website=False, sitemap=False)
    def technician_app(self, **kwargs):
        path = get_module_resource('unit_maintenance', 'static', 'src', 'technician_app.html')
        with open(path, 'rb') as app_file:
            content = app_file.read()
        return request.make_response(content, headers=[
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
