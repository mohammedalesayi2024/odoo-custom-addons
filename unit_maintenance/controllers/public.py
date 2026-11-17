from datetime import timedelta

from odoo import fields, http
from odoo.http import request

from ..models.utils import normalize_phone
from .common import json_response, read_json


class PublicComplaintAPI(http.Controller):
    """شكوى العميل بدون تسجيل دخول: رقم الجوال ← OTP ← اختيار الوحدة ← إرسال المشكلة."""

    @http.route('/unit_maintenance/api/complaint/otp/request', type='http', auth='public',
                methods=['POST'], csrf=False)
    def otp_request(self, **kw):
        body = read_json()
        status, payload = request.env['unit.maintenance.otp'].sudo().request_code(
            body.get('phone'), request.httprequest.remote_addr)
        return json_response(payload, status)

    @http.route('/unit_maintenance/api/complaint/otp/verify', type='http', auth='public',
                methods=['POST'], csrf=False)
    def otp_verify(self, **kw):
        body = read_json()
        status, payload = request.env['unit.maintenance.otp'].sudo().verify_code(
            body.get('phone'), body.get('code'))
        return json_response(payload, status)

    @http.route('/unit_maintenance/api/complaint/submit', type='http', auth='public',
                methods=['POST'], csrf=False)
    def submit(self, **kw):
        body = read_json()
        env = request.env
        otp = env['unit.maintenance.otp'].sudo()
        phone = body.get('phone')
        key = normalize_phone(phone)
        record = otp.consume_token(phone, body.get('token'))
        if not record:
            return json_response({'ok': False, 'error': 'invalid_token',
                                  'message': 'انتهت جلسة التحقق، أعد إدخال رقم الجوال'}, 401)
        description = (body.get('description') or '').strip()
        if not 5 <= len(description) <= 2000:
            return json_response({'ok': False, 'error': 'invalid_description',
                                  'message': 'اكتب وصفاً للمشكلة (5 أحرف على الأقل)'}, 400)
        try:
            unit_id = int(body.get('unit_id'))
        except (TypeError, ValueError):
            unit_id = 0
        units = otp._units_for_key(key)
        unit = units.filtered(lambda u: u.id == unit_id)
        if not unit:
            return json_response({'ok': False, 'error': 'invalid_unit', 'message': 'الوحدة غير صحيحة'}, 400)
        complaint_model = env['unit.maintenance.complaint'].sudo()
        limit = int(otp._cfg('max_complaints_per_day', '5'))
        since = fields.Datetime.now() - timedelta(days=1)
        if complaint_model.search_count([('phone_key', '=', key), ('create_date', '>=', since)]) >= limit:
            return json_response({'ok': False, 'error': 'rate_limited',
                                  'message': 'تجاوزت عدد الشكاوى المسموح اليوم، تواصل مع الإدارة'}, 429)
        complaint = complaint_model.create({
            'phone': phone, 'phone_key': key, 'unit_id': unit.id, 'description': description,
            'ip_address': request.httprequest.remote_addr})
        record.state = 'used'
        return json_response({'ok': True, 'ref': complaint.name,
                              'message': 'تم استلام الشكوى وستتم مراجعتها من إدارة الصيانة'})

    @http.route('/unit_maintenance/report/<int:request_id>/<string:token>', type='http', auth='public')
    def public_report(self, request_id, token, **kw):
        rec = request.env['unit.maintenance.request'].sudo().browse(request_id).exists()
        if not rec or not token or rec.access_token != token or rec.state != 'done':
            return request.not_found()
        pdf, _fmt = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'unit_maintenance.action_report_unit_request', rec.ids)
        return request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'inline; filename="%s.pdf"' % rec.name)])
