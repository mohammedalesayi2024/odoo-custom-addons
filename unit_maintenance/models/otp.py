import hashlib
import hmac
import logging
import secrets
import requests
from datetime import timedelta

from odoo import api, fields, models

from .utils import normalize_phone

_logger = logging.getLogger(__name__)


class UnitMaintenanceOtp(models.Model):
    """رموز التحقق لشاشة الشكوى. تُولَّد وتُتحقق من جهة Odoo فقط، ولا يُخزَّن الرمز نفسه."""
    _name = 'unit.maintenance.otp'
    _description = 'رمز تحقق شكوى العميل'
    _order = 'id desc'

    phone_key = fields.Char(index=True, required=True)
    ip = fields.Char(index=True)
    state = fields.Selection(
        [('pending', 'بانتظار الإدخال'), ('verified', 'تم التحقق'), ('used', 'مستخدم'),
         ('expired', 'منتهي'), ('locked', 'مقفل'), ('unregistered', 'رقم غير مسجل')],
        default='pending', index=True)
    code_hash = fields.Char()
    attempts = fields.Integer()
    expires = fields.Datetime()
    token_hash = fields.Char(index=True)
    token_expires = fields.Datetime()

    # ------------------------------------------------------------------ helpers
    def _cfg(self, key, default):
        return self.env['ir.config_parameter'].sudo().get_param('unit_maintenance.' + key, default)

    def _hash(self, code):
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret') or 'unit_maintenance'
        msg = '%s:%s:%s' % (self.id, self.phone_key, code)
        return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @api.model
    def _units_for_key(self, key):
        partners = self.env['res.partner'].sudo().search([('maintenance_phone_keys', 'like', ',%s,' % key)])
        if not partners:
            return self.env['unit.maintenance.unit']
        owners = partners | partners.commercial_partner_id
        return self.env['unit.maintenance.unit'].sudo().search([('owner_id', 'in', owners.ids)])

    @api.model
    def units_payload(self, units):
        return [{
            'id': u.id,
            'building': u.building_id.name, 'building_code': u.building_id.code or '',
            'unit': u.number, 'owner': u.owner_id.name,
            'label': 'عمارة %s · وحدة %s · المالك: %s' % (u.building_id.name, u.number, u.owner_id.name),
        } for u in units]

    def _send_sms(self, key, code):
        body = 'رمز التحقق لتقديم شكوى الصيانة: %s. صالح %s دقائق.' % (
            code, self._cfg('otp_ttl_minutes', '5'))
        if self._cfg('otp_test_mode', '0') == '1':
            _logger.warning('OTP TEST MODE: phone=%s code=%s', key, code)
            return

        provider = self._cfg('sms_provider', 'taqnyat')
        if provider == 'taqnyat':
            token = self._cfg('taqnyat_api_token', '')
            sender = self._cfg('taqnyat_sender', '')
            if not token or not sender:
                raise ValueError('Taqnyat API token or sender name is not configured')

            # Taqnyat expects Saudi mobile numbers in international format
            # without "+" or "00", e.g. 9665XXXXXXXX.
            country_code = self._cfg('default_country_code', '966')
            number = '%s%s' % (country_code, key)
            response = requests.post(
                'https://api.taqnyat.sa/v1/messages',
                headers={
                    'Authorization': 'Bearer %s' % token,
                    'Content-Type': 'application/json; charset=UTF-8',
                    'Accept': 'application/json',
                },
                json={
                    'sender': sender,
                    'recipients': [number],
                    'body': body,
                },
                timeout=20,
            )
            try:
                result = response.json()
            except ValueError:
                result = {'message': response.text[:500]}
            if response.status_code not in (200, 201) or result.get('statusCode') not in (None, 200, 201):
                raise ValueError('Taqnyat SMS API error (%s): %s' % (
                    response.status_code, result.get('message', result)))
            if result.get('rejected') and result.get('rejected') not in ('[]', [], None):
                raise ValueError('Taqnyat rejected recipient: %s' % result.get('rejected'))
            return result

        # Optional fallback to Odoo's configured SMS gateway.
        number = '+%s%s' % (self._cfg('default_country_code', '966'), key)
        self.env['sms.sms'].sudo().create({'number': number, 'body': body}).send()

    # ------------------------------------------------------------------ API
    @api.model
    def request_code(self, phone_raw, ip=None):
        """يعيد (status_code, payload)."""
        key = normalize_phone(phone_raw)
        if not 8 <= len(key) <= 12:
            return 400, {'ok': False, 'error': 'invalid_phone', 'message': 'رقم الجوال غير صحيح'}
        now = fields.Datetime.now()
        hour_ago = now - timedelta(hours=1)
        if ip and self.search_count([('ip', '=', ip), ('create_date', '>=', hour_ago)]) >= int(self._cfg('otp_max_per_ip_hour', '10')):
            return 429, {'ok': False, 'error': 'rate_limited', 'message': 'محاولات كثيرة، حاول لاحقاً'}
        if not self._units_for_key(key):
            self.create({'phone_key': key, 'ip': ip, 'state': 'unregistered'})
            if self._cfg('reveal_unregistered', '1') == '1':
                return 404, {'ok': False, 'error': 'not_registered',
                             'message': 'هذا الرقم غير مسجّل لدينا، تواصل مع إدارة الصيانة'}
            return 200, {'ok': True, 'message': 'إذا كان الرقم مسجلاً فسيصلك رمز التحقق'}
        if self.search_count([('phone_key', '=', key), ('state', '!=', 'unregistered'),
                              ('create_date', '>=', hour_ago)]) >= int(self._cfg('otp_max_per_hour', '3')):
            return 429, {'ok': False, 'error': 'rate_limited', 'message': 'تجاوزت عدد الرموز المسموح، حاول بعد ساعة'}
        self.search([('phone_key', '=', key), ('state', '=', 'pending')]).write({'state': 'expired'})
        length = int(self._cfg('otp_length', '4'))
        code = ''.join(secrets.choice('0123456789') for i in range(length))
        rec = self.create({'phone_key': key, 'ip': ip, 'state': 'pending',
                           'expires': now + timedelta(minutes=int(self._cfg('otp_ttl_minutes', '5')))})
        rec.code_hash = rec._hash(code)
        try:
            rec._send_sms(key, code)
        except Exception:
            _logger.exception('Failed to send OTP SMS')
            return 502, {'ok': False, 'error': 'sms_failed', 'message': 'تعذر إرسال الرسالة، حاول لاحقاً'}
        return 200, {'ok': True, 'message': 'تم إرسال رمز التحقق', 'length': length}

    @api.model
    def verify_code(self, phone_raw, code):
        key = normalize_phone(phone_raw)
        now = fields.Datetime.now()
        rec = self.search([('phone_key', '=', key), ('state', '=', 'pending')], order='id desc', limit=1)
        if not rec or not rec.expires or rec.expires < now:
            if rec:
                rec.state = 'expired'
            return 400, {'ok': False, 'error': 'expired', 'message': 'انتهت صلاحية الرمز، اطلب رمزاً جديداً'}
        max_attempts = int(self._cfg('otp_max_attempts', '5'))
        rec.attempts += 1
        if not hmac.compare_digest(rec.code_hash or '', rec._hash(str(code or '').strip())):
            if rec.attempts >= max_attempts:
                rec.state = 'locked'
                return 429, {'ok': False, 'error': 'locked', 'message': 'تم إيقاف الرمز، اطلب رمزاً جديداً'}
            return 400, {'ok': False, 'error': 'invalid_code', 'message': 'الرمز غير صحيح',
                         'attempts_left': max_attempts - rec.attempts}
        token = secrets.token_urlsafe(32)
        rec.write({'state': 'verified', 'token_hash': self._hash_token(token),
                   'token_expires': now + timedelta(minutes=int(self._cfg('token_ttl_minutes', '30')))})
        return 200, {'ok': True, 'token': token, 'units': self.units_payload(self._units_for_key(key))}

    @api.model
    def consume_token(self, phone_raw, token):
        """يعيد سجل OTP المتحقق منه إن كان الرمز المميز صالحاً، وإلا فارغاً."""
        key = normalize_phone(phone_raw)
        if not token:
            return self.browse()
        rec = self.search([('phone_key', '=', key), ('state', '=', 'verified'),
                           ('token_hash', '=', self._hash_token(token)),
                           ('token_expires', '>=', fields.Datetime.now())], limit=1)
        return rec

    @api.autovacuum
    def _gc_otp(self):
        self.search([('create_date', '<', fields.Datetime.now() - timedelta(days=7))]).unlink()
