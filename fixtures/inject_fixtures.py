# -*- coding: utf-8 -*-

from os import path
import json
from time import time
import pytest
from mock import Mock

PWD = path.dirname(path.realpath(__file__))
FIXTURE_DATA_PATH = path.join(PWD, 'data')


@pytest.fixture
def old_prepare_yaml():
    yaml_file = path.join(FIXTURE_DATA_PATH, 'old_prepare.yaml')
    with open(yaml_file) as f:
        meta_yaml = f.read()
    return meta_yaml


@pytest.fixture
def new_prepare_yaml():
    yaml_file = path.join(FIXTURE_DATA_PATH, 'new_prepare.yaml')
    with open(yaml_file) as f:
        meta_yaml = f.read()
    return meta_yaml


@pytest.fixture
def healthcheck_yaml():
    yaml_file = path.join(FIXTURE_DATA_PATH, 'healthcheck.yaml')
    with open(yaml_file) as f:
        meta_yaml = f.read()
    return meta_yaml


@pytest.fixture
def release_yaml():
    yaml_file = path.join(FIXTURE_DATA_PATH, 'release.yaml')
    with open(yaml_file) as f:
        meta_yaml = f.read()
    return meta_yaml


@pytest.fixture
def validation_yaml():
    yaml_file = path.join(FIXTURE_DATA_PATH, 'for_validate.yaml')
    with open(yaml_file) as f:
        meta_yaml = f.read()
    return meta_yaml
