#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
from lain_sdk.yaml.validator import validate

def test_lain_yaml_validator_smoke(validation_yaml):
    source_data = yaml.load(validation_yaml)
    valid, msg = validate(source_data)
    assert valid
