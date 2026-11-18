from pathlib import Path

from odoo import http
from odoo.http import request


class TechnicianApp(http.Controller):

    @http.route('/unit_maintenance/app', type='http', auth='public', methods=['GET'],
                website=False, sitemap=False)
    def technician_app(self, **kwargs):
        # Resolve the HTML file relative to this controller for Odoo 19.
        module_dir = Path(__file__).resolve().parent.parent
        app_path = module_dir / 'static' / 'src' / 'technician_app.html'
        content = app_path.read_bytes()
        return request.make_response(content, headers=[
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
