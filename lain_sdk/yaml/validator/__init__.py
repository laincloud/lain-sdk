# -*- coding: utf-8 -*-

import jsonschema
from .schema import schema


def validate(source_data):
    try:
        jsonschema.validate(source_data, schema)
        return True, 'ok'
    except Exception as e:
        return False, str(e)
