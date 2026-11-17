import re


def normalize_phone(raw):
    """يحوّل أي صيغة جوال (0502441702 / +966502441702 / 00966...) إلى المفتاح 502441702."""
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('966'):
        digits = digits[3:]
    return digits.lstrip('0')


def group_users(env, xmlid):
    """مستخدمو مجموعة (يتوافق مع تسمية الحقل بين الإصدارات)."""
    group = env.ref(xmlid)
    return group['user_ids'] if 'user_ids' in group._fields else group['users']
