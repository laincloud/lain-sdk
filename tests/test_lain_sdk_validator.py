#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import yaml
from lain_sdk.yaml.validator import validate


def test_lain_yaml_validator_smoke(validation_yaml):
    source_data = yaml.load(validation_yaml)
    valid, msg = validate(source_data)
    assert valid


@pytest.mark.parametrize("data, want", [
    (
        """
appname: test
build:
  base: centos
  script:
    - echo "Success"
web:
  cmd: echo "Hello"
  memory: 128M
        """,
        True
    ),
    (
        """
appname: test
build:
  base: centos
  script:
    - echo "Success"
web:
  cmd: echo "Hello"
  memory: 2G
        """,
        True
    ),
    (
        """
appname: test
build:
  base: centos
  script:
    - echo "Success"
web:
  cmd: echo "Hello"
  memory: 128
        """,
        False
    ),
    (
        """
appname: test
build:
  base: centos
  script:
    - echo "Success"
web:
  cmd: echo "Hello"
  memory: 128a
        """,
        False
    ),
    (
        """
appname: test
build:
  base: centos
  script:
    - echo "Success"
web:
  cmd: echo "Hello"
  memory: M
        """,
        False
    ),
])
def test_memory_format(data, want):
    lain_config = yaml.safe_load(data)
    valid, msg = validate(lain_config)
    assert valid == want
