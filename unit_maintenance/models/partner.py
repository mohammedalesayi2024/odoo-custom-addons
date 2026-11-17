from odoo import api, fields, models

from .utils import normalize_phone


class ResPartner(models.Model):
    _inherit = 'res.partner'

    maintenance_phone_keys = fields.Char(
        compute='_compute_maintenance_phone_keys', store=True, index=True, copy=False,
        help='أرقام الجوال بعد التطبيع، تُستخدم لمطابقة رقم العميل في شاشة الشكوى.')

    @api.depends('phone')
    def _compute_maintenance_phone_keys(self):
        for partner in self:
            raws = [partner.phone]
            if 'mobile' in partner._fields:
                raws.append(partner['mobile'])
            keys = {normalize_phone(r) for r in raws if r} - {''}
            partner.maintenance_phone_keys = (',' + ','.join(sorted(keys)) + ',') if keys else False

    def write(self, vals):
        res = super().write(vals)
        if 'mobile' in vals and 'mobile' in self._fields:
            self._compute_maintenance_phone_keys()
        return res
