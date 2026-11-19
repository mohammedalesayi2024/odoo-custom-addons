
import hashlib
import hmac
import logging
import secrets
import requests
import re

from datetime import timedelta

from odoo import api, fields, models

from .utils import normalize_phone

_logger = logging.getLogger(__name__)


class UnitMaintenanceOtp(models.Model):
    """OTP لشكاوى العملاء. ينشأ ويتحقق منه داخل Odoo."""
    _name = 'unit.maintenance.otp'
    _description = 'رمز تحقق شكوى العميل'
    _order = 'id desc'

    phone_key = fields.Char(index=True, required=True)
    ip = fields.Char(index=True)

    state = fields.Selection(
        [
            ('pending', 'بانتظار الإدخال'),
            ('verified', 'تم التحقق'),
            ('used', 'مستخدم'),
            ('expired', 'منتهي'),
            ('locked', 'مقفل'),
            ('unregistered', 'رقم غير مسجل'),
        ],
        default='pending',
        index=True,
    )

    code_hash = fields.Char()
    attempts = fields.Integer()
    expires = fields.Datetime()
    token_hash = fields.Char(index=True)
    token_expires = fields.Datetime()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _cfg(self, key, default):
        return self.env['ir.config_parameter'].sudo().get_param(
            'unit_maintenance.' + key, default
        )

    def _hash(self, code):
        secret = (
            self.env['ir.config_parameter'].sudo().get_param(
                'database.secret'
            ) or 'unit_maintenance'
        )
        msg = '%s:%s:%s' % (self.id, self.phone_key, code)

        return hmac.new(
            secret.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def _format_sms_number(self, key):
        """توحيد رقم الجوال بصيغة دولية دون تكرار مفتاح الدولة."""
        digits = re.sub(r'\D', '', str(key or ''))
        country_code = re.sub(
            r'\D', '',
            str(self._cfg('default_country_code', '966'))
        )

        if digits.startswith('00'):
            digits = digits[2:]

        if digits.startswith(country_code):
            return digits

        if digits.startswith('0'):
            digits = digits[1:]

        return country_code + digits

    @api.model
    def _units_for_key(self, key):
        partners = self.env['res.partner'].sudo().search([
            ('maintenance_phone_keys', 'like', ',%s,' % key)
        ])

        if not partners:
            return self.env['unit.maintenance.unit']

        owners = partners | partners.commercial_partner_id

        return self.env['unit.maintenance.unit'].sudo().search([
            ('owner_id', 'in', owners.ids)
        ])

    @api.model
    def units_payload(self, units):
        return [{
            'id': u.id,
            'building': u.building_id.name,
            'building_code': u.building_id.code or '',
            'unit': u.number,
            'owner': u.owner_id.name,
            'label': 'عمارة %s · وحدة %s · المالك: %s' % (
                u.building_id.name,
                u.number,
                u.owner_id.name
            ),
        } for u in units]

    # ---------------------------------------------------------
    # SMS Sending
    # ---------------------------------------------------------

    def _send_sms(self, key, code):
        ttl = int(self._cfg('otp_ttl_minutes', '5'))

        # Odoo generates the OTP and builds the actual SMS content.
        body = (
            'رمز التحقق لتقديم شكوى الصيانة: %s. '
            'صالح لمدة %s دقائق.'
        ) % (code, ttl)

        if self._cfg('otp_test_mode', '0') == '1':
            _logger.warning(
                'OTP TEST MODE enabled. SMS was not sent. '
                'phone_suffix=%s',
                str(key)[-4:]
            )
            return {'test_mode': True}

        provider = self._cfg('sms_provider', 'taqnyat')

        if provider == 'taqnyat':
            token = self._cfg('taqnyat_api_token', '')
            sender = self._cfg('taqnyat_sender', '')

            if not token or not sender:
                raise ValueError(
                    'Taqnyat API token or sender name is not configured'
                )

            number = self._format_sms_number(key)

            payload = {
                'sender': sender,
                'recipients': [number],
                'body': body,
            }

            _logger.info(
                'OTP: sending dynamic SMS through Taqnyat. '
                'recipient_suffix=%s',
                number[-4:]
            )

            try:
                response = requests.post(
                    'https://api.taqnyat.sa/v1/messages',
                    headers={
                        'Authorization': 'Bearer %s' % token,
                        'Content-Type': 'application/json; charset=UTF-8',
                        'Accept': 'application/json',
                    },
                    json=payload,
                    timeout=20,
                )
            except requests.RequestException as exc:
                _logger.error(
                    'OTP: connection to Taqnyat failed: %s',
                    type(exc).__name__
                )
                raise ValueError(
                    'Unable to connect to Taqnyat SMS service'
                )

            try:
                result = response.json()
            except ValueError:
                result = {}

            # Log response metadata only. Never log token or OTP.
            _logger.info(
                'OTP: Taqnyat returned HTTP status %s',
                response.status_code
            )

            if response.status_code not in (200, 201):
                _logger.error(
                    'OTP: Taqnyat rejected SMS. HTTP status=%s',
                    response.status_code
                )
                raise ValueError(
                    'Taqnyat SMS API rejected the request (HTTP %s)'
                    % response.status_code
                )

            if not isinstance(result, dict):
                raise ValueError(
                    'Unexpected response from Taqnyat'
                )

            status_code = result.get('statusCode')

            if status_code not in (None, 200, 201):
                raise ValueError(
                    'Taqnyat returned an unsuccessful status'
                )

            rejected = result.get('rejected')

            if rejected and rejected not in ('[]', [], None):
                raise ValueError(
                    'Taqnyat rejected the recipient number'
                )

            _logger.info(
                'OTP: Taqnyat accepted the SMS request. '
                'recipient_suffix=%s',
                number[-4:]
            )

            return result

        # Fallback to Odoo SMS gateway.
        number = '+%s' % self._format_sms_number(key)

        sms = self.env['sms.sms'].sudo().create({
            'number': number,
            'body': body,
        })

        sms.send()

        return True

    # ---------------------------------------------------------
    # Request OTP
    # ---------------------------------------------------------

    @api.model
    def request_code(self, phone_raw, ip=None):
        """Create OTP, send it, and return the request result."""

        key = normalize_phone(phone_raw)

        if not 8 <= len(key) <= 12:
            return 400, {
                'ok': False,
                'error': 'invalid_phone',
                'message': 'رقم الجوال غير صحيح',
            }

        now = fields.Datetime.now()
        hour_ago = now - timedelta(hours=1)

        max_ip = int(self._cfg('otp_max_per_ip_hour', '10'))
        max_phone = int(self._cfg('otp_max_per_hour', '3'))

        if ip and self.search_count([
            ('ip', '=', ip),
            ('create_date', '>=', hour_ago),
        ]) >= max_ip:
            return 429, {
                'ok': False,
                'error': 'rate_limited',
                'message': 'محاولات كثيرة، حاول لاحقاً',
            }

        units = self._units_for_key(key)

        if not units:
            self.create({
                'phone_key': key,
                'ip': ip,
                'state': 'unregistered',
            })

            if self._cfg('reveal_unregistered', '1') == '1':
                return 404, {
                    'ok': False,
                    'error': 'not_registered',
                    'message': 'هذا الرقم غير مسجّل لدينا، تواصل مع إدارة الصيانة',
                }

            return 200, {
                'ok': True,
                'message': 'إذا كان الرقم مسجلاً فسيصلك رمز التحقق',
            }

        if self.search_count([
            ('phone_key', '=', key),
            ('state', '!=', 'unregistered'),
            ('create_date', '>=', hour_ago),
        ]) >= max_phone:
            return 429, {
                'ok': False,
                'error': 'rate_limited',
                'message': 'تجاوزت عدد الرموز المسموح، حاول بعد ساعة',
            }

        # Expire previous pending codes.
        self.search([
            ('phone_key', '=', key),
            ('state', '=', 'pending'),
        ]).write({
            'state': 'expired',
        })

        length = int(self._cfg('otp_length', '4'))

        if not 4 <= length <= 8:
            length = 4

        code = ''.join(
            secrets.choice('0123456789')
            for _ in range(length)
        )

        rec = self.create({
            'phone_key': key,
            'ip': ip,
            'state': 'pending',
            'expires': now + timedelta(
                minutes=int(self._cfg('otp_ttl_minutes', '5'))
            ),
        })

        rec.code_hash = rec._hash(code)

        try:
            # Send the exact dynamically generated code.
            rec._send_sms(key, code)

        except Exception:
            _logger.exception(
                'OTP: SMS sending failed. record_id=%s',
                rec.id
            )

            # Do not leave an unsent OTP valid.
            rec.write({
                'state': 'expired',
                'code_hash': False,
            })

            return 502, {
                'ok': False,
                'error': 'sms_failed',
                'message': 'تعذر إرسال الرسالة، حاول لاحقاً',
            }

        return 200, {
            'ok': True,
            'message': 'تم إرسال رمز التحقق',
            'length': length,
        }

    # ---------------------------------------------------------
    # Verify OTP
    # ---------------------------------------------------------

    @api.model
    def verify_code(self, phone_raw, code):
        key = normalize_phone(phone_raw)
        now = fields.Datetime.now()

        rec = self.search([
            ('phone_key', '=', key),
            ('state', '=', 'pending'),
        ], order='id desc', limit=1)

        if not rec or not rec.expires or rec.expires < now:
            if rec:
                rec.state = 'expired'

            return 400, {
                'ok': False,
                'error': 'expired',
                'message': 'انتهت صلاحية الرمز، اطلب رمزاً جديداً',
            }

        max_attempts = int(self._cfg('otp_max_attempts', '5'))

        rec.attempts += 1

        submitted_code = str(code or '').strip()

        if not hmac.compare_digest(
            rec.code_hash or '',
            rec._hash(submitted_code)
        ):
            if rec.attempts >= max_attempts:
                rec.state = 'locked'

                return 429, {
                    'ok': False,
                    'error': 'locked',
                    'message': 'تم إيقاف الرمز، اطلب رمزاً جديداً',
                }

            return 400, {
                'ok': False,
                'error': 'invalid_code',
                'message': 'الرمز غير صحيح',
                'attempts_left': max_attempts - rec.attempts,
            }

        token = secrets.token_urlsafe(32)

        rec.write({
            'state': 'verified',
            'token_hash': self._hash_token(token),
            'token_expires': now + timedelta(
                minutes=int(self._cfg('token_ttl_minutes', '30'))
            ),
        })

        return 200, {
            'ok': True,
            'token': token,
            'units': self.units_payload(
                self._units_for_key(key)
            ),
        }

    # ---------------------------------------------------------
    # Consume verification token
    # ---------------------------------------------------------

    @api.model
    def consume_token(self, phone_raw, token):
        """Return verified OTP record if token is valid."""

        key = normalize_phone(phone_raw)

        if not token:
            return self.browse()

        return self.search([
            ('phone_key', '=', key),
            ('state', '=', 'verified'),
            ('token_hash', '=', self._hash_token(token)),
            ('token_expires', '>=', fields.Datetime.now()),
        ], limit=1)

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    @api.autovacuum
    def _gc_otp(self):
        self.search([
            ('create_date', '<',
             fields.Datetime.now() - timedelta(days=7)),
        ]).unlink()
