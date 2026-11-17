import base64
import binascii
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

from odoo import Command, fields, http
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request

from ..models.utils import normalize_phone
from .common import json_response, read_json

_logger = logging.getLogger(__name__)
TECH_GROUP = 'unit_maintenance.group_unit_maintenance_technician'
MAX_IMAGE_BYTES = 6 * 1024 * 1024


def _authenticate(login, password):
    credential = {'type': 'password', 'login': login, 'password': password}
    try:
        info = request.session.authenticate(request.env, credential)  # 18+/19
    except TypeError:
        info = request.session.authenticate(request.db, credential)   # الإصدارات الأقدم
    return info['uid'] if isinstance(info, dict) else info


def _image(value):
    try:
        raw = base64.b64decode(value or '', validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError('صورة غير صالحة')
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValidationError('حجم الصورة غير مقبول')
    return value


def _local(env, dt):
    return fields.Datetime.context_timestamp(env.user, dt) if dt else None


def _brief(rec):
    created = _local(rec.env, rec.request_date)
    visit = _local(rec.env, rec.visit_date)
    return {
        'id': rec.id, 'ref': rec.name, 'type': rec.request_type, 'state': rec.state,
        'building': rec.building_id.name, 'unit': rec.unit_id.number, 'owner': rec.owner_id.name,
        'phone': rec.contact_phone or '',
        'date': created.strftime('%Y-%m-%d') if created else '', 'time': created.strftime('%H:%M') if created else '',
        'visit': visit.strftime('%Y-%m-%d %H:%M') if visit else '',
    }


def _detail(rec):
    external = rec.request_type == 'external'
    show_price = rec.price_approved
    has = bool(rec.line_ids)
    priced = rec.price_approved
    data = _brief(rec)
    key = normalize_phone(rec.contact_phone)
    country = rec.env['ir.config_parameter'].sudo().get_param('unit_maintenance.default_country_code', '966')
    data.update({
        'description': rec.description or '',
        'cost_bearer': rec.cost_bearer,
        'cost_bearer_label': 'شركة أديار' if rec.request_type == 'internal' else 'العميل',
        'warranty': {'delivery_date': rec.delivery_date.isoformat() if rec.delivery_date else None,
                     'months': rec.warranty_months,
                     'end_date': rec.warranty_end.isoformat() if rec.warranty_end else None,
                     'state': rec.warranty_state},
        'lines': [{'id': l.id, 'product_id': l.product_id.id, 'name': l.name, 'quantity': l.quantity,
                   'price': l.price_unit if show_price else None,
                   'subtotal': l.subtotal if show_price else None} for l in rec.line_ids],
        'steps': {'products': has, 'priced': priced, 'signed': bool(rec.signature)},
        'can_start': has and priced and bool(rec.signature) and rec.state == 'assigned',
        'awaiting_price': rec.state == 'awaiting_price',
        'totals': {'untaxed': rec.amount_untaxed, 'tax': rec.amount_tax, 'total': rec.amount_total}
        if rec.price_approved else None,
        'photos': [{'id': p.id, 'kind': p.kind, 'note': p.note or ''} for p in rec.photo_ids],
        'report': rec.report_text or '',
        'start': rec.start_datetime.isoformat() if rec.start_datetime else None,
        'duration': rec.duration_text, 'report_sent': rec.report_sent,
        'tel': 'tel:%s' % (rec.contact_phone or ''),
        'wa': 'https://wa.me/%s%s' % (country, key) if key else '',
        'map': rec.building_id.map_url or 'https://www.google.com/maps/search/?api=1&query=%s' % quote(
            '%s %s' % (rec.building_id.name or '', rec.building_id.address or '')),
    })
    return data


class TechnicianAPI(http.Controller):
    """واجهة تطبيق الفني. تسجيل الدخول يعيد كوكي الجلسة ويُرسَل مع كل الطلبات التالية."""

    @http.route('/unit_maintenance/api/login', type='http', auth='public', methods=['POST'], csrf=False)
    def login(self, **kw):
        body = read_json()
        try:
            uid = _authenticate(body.get('login'), body.get('password'))
        except AccessDenied:
            return json_response({'ok': False, 'message': 'بيانات الدخول غير صحيحة'}, 401)
        user = request.env['res.users'].sudo().browse(uid)
        if not user.has_group(TECH_GROUP):
            request.session.logout()
            return json_response({'ok': False, 'message': 'هذا الحساب ليس حساب فني'}, 403)
        return json_response({'ok': True, 'name': user.name, 'uid': uid, 'session_id': request.session.sid})

    @http.route('/unit_maintenance/api/logout', type='http', auth='public', methods=['POST'], csrf=False)
    def logout(self, **kw):
        request.session.logout()
        return json_response({'ok': True})

    @http.route('/unit_maintenance/api/<string:action>', type='http', auth='public', methods=['POST'], csrf=False)
    def dispatch(self, action, **kw):
        uid = request.session.uid
        if not uid:
            return json_response({'ok': False, 'message': 'انتهت الجلسة، سجّل الدخول'}, 401)
        request.update_env(user=uid)
        env = request.env
        handler = getattr(self, '_api_' + action, None)
        if not handler or not env.user.has_group(TECH_GROUP):
            return json_response({'ok': False, 'message': 'غير مصرح'}, 403)
        try:
            result = handler(env, read_json())
        except (UserError, ValidationError) as exc:
            env.cr.rollback()
            return json_response({'ok': False, 'message': str(exc)}, 400)
        except AccessError:
            env.cr.rollback()
            return json_response({'ok': False, 'message': 'غير مصرح بهذا الإجراء'}, 403)
        result['ok'] = True
        return json_response(result)

    # ------------------------------------------------------------------ helpers
    def _job(self, env, body):
        try:
            rec = env['unit.maintenance.request'].browse(int(body.get('id'))).exists()
        except (TypeError, ValueError):
            rec = None
        if not rec:
            raise UserError('الطلب غير موجود')
        if rec.technician_id != env.user:
            raise AccessError('not assigned')
        return rec

    def _base_domain(self, env, body):
        domain = [('technician_id', '=', env.user.id), ('state', '!=', 'cancel')]
        for key, op in (('date_from', '>='), ('date_to', '<=')):
            if body.get(key):
                try:
                    day = datetime.strptime(body[key], '%Y-%m-%d')
                except ValueError:
                    continue
                if key == 'date_to':
                    day += timedelta(days=1) - timedelta(seconds=1)
                domain.append(('request_date', op, day))
        text = (body.get('q') or '').strip()
        if text:
            domain += ['|', '|', '|', ('unit_id.number', 'ilike', text), ('building_id.name', 'ilike', text),
                       ('owner_id.name', 'ilike', text), ('name', 'ilike', text)]
        return domain

    # ------------------------------------------------------------------ endpoints
    def _api_dashboard(self, env, body):
        model = env['unit.maintenance.request']
        base = self._base_domain(env, body)
        kind = body.get('type')
        if kind in ('internal', 'external'):
            base.append(('request_type', '=', kind))
        total = model.search_count(base)
        done = model.search_count(base + [('state', '=', 'done')])
        n_int = model.search_count(base + [('request_type', '=', 'internal')])
        n_ext = model.search_count(base + [('request_type', '=', 'external')])
        open_domain = self._base_domain(env, {}) + [('state', 'not in', ('done', 'cancel'))]
        return {
            'total': total, 'done': done, 'pending': total - done,
            'internal_pct': round(100.0 * n_int / total) if total else 0,
            'external_pct': round(100.0 * n_ext / total) if total else 0,
            'open_internal': model.search_count(open_domain + [('request_type', '=', 'internal')]),
            'open_external': model.search_count(open_domain + [('request_type', '=', 'external')]),
        }

    def _api_jobs(self, env, body):
        domain = self._base_domain(env, body) + [('state', 'not in', ('done', 'cancel'))]
        if body.get('type') in ('internal', 'external'):
            domain.append(('request_type', '=', body['type']))
        jobs = env['unit.maintenance.request'].search(domain, order='visit_date, id', limit=200)
        return {'jobs': [_brief(j) for j in jobs]}

    def _api_job(self, env, body):
        return {'job': _detail(self._job(env, body))}

    def _api_done(self, env, body):
        domain = self._base_domain(env, body) + [('state', '=', 'done')]
        jobs = env['unit.maintenance.request'].search(domain, order='end_datetime desc', limit=200)
        return {'jobs': [dict(_brief(j), duration=j.duration_text, report=j.report_text or '',
                              report_sent=j.report_sent) for j in jobs]}

    def _api_products(self, env, body):
        domain = [('sale_ok', '=', True)]
        if body.get('q'):
            domain.append(('name', 'ilike', body['q']))
        products = env['product.product'].search(domain, limit=50)
        return {'products': [{'id': p.id, 'name': p.display_name} for p in products]}

    def _api_set_products(self, env, body):
        rec = self._job(env, body)
        rec._check_state('assigned', 'awaiting_price')
        wanted = {}
        for item in body.get('lines') or []:
            try:
                wanted[int(item['product_id'])] = max(float(item.get('quantity') or 1), 0.01)
            except (KeyError, TypeError, ValueError):
                raise ValidationError('بيانات المنتجات غير صحيحة')
        products = env['product.product'].search([('id', 'in', list(wanted)), ('sale_ok', '=', True)])
        commands = [Command.delete(l.id) for l in rec.line_ids]
        commands += [Command.create({'product_id': p.id, 'quantity': wanted[p.id]}) for p in products]
        rec.write({'line_ids': commands})
        if rec.state == 'awaiting_price':
            rec.state = 'assigned'
        return {'job': _detail(rec)}

    def _api_request_price(self, env, body):
        rec = self._job(env, body)
        rec.action_request_price()
        return {'job': _detail(rec)}

    def _api_signature(self, env, body):
        rec = self._job(env, body)
        if body.get('clear'):
            rec.write({'signature': False, 'signed_date': False})
        else:
            rec.action_set_signature(_image(body.get('signature')))
        return {'job': _detail(rec)}

    def _api_start(self, env, body):
        rec = self._job(env, body)
        rec.action_start()
        return {'job': _detail(rec)}

    def _api_photo(self, env, body):
        rec = self._job(env, body)
        rec._check_state('assigned', 'in_progress')
        if body.get('kind') not in ('before', 'after'):
            raise ValidationError('نوع الصورة غير صحيح')
        env['unit.maintenance.photo'].create({
            'request_id': rec.id, 'kind': body['kind'], 'image': _image(body.get('image')),
            'note': (body.get('note') or '')[:200]})
        return {'job': _detail(rec)}

    def _api_finish(self, env, body):
        rec = self._job(env, body)
        rec.action_finish(body.get('report'))
        return {'job': _detail(rec)}

    def _api_send_report(self, env, body):
        rec = self._job(env, body)
        return {'result': rec._send_report(body.get('method') or 'wa'), 'job': _detail(rec)}
