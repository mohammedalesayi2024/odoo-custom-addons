import json

from odoo.http import request


def read_json():
    try:
        data = json.loads(request.httprequest.get_data(as_text=True) or '{}')
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def json_response(payload, status=200):
    return request.make_json_response(payload, status=status)
