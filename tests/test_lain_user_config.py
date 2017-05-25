# -*- coding: utf-8

import pytest
from lain_sdk.yaml.lain_user_config import LainUserConfig


def test_lain_user_conf_base_empty_smoke(tmpdir):
    etc_path = tmpdir.mkdir("etc").mkdir("lain")
    print etc_path.strpath
    assert LainUserConfig.get_config_from(etc_path.strpath) == {}


def test_lain_user_conf_base_smoke(tmpdir):
    p = tmpdir.mkdir("etc").mkdir("lain").join("global.conf.yaml")
    p.write("private_docker_registry: registry.lain.local")
    p_config = LainUserConfig.get_config_from(p.strpath)
    assert p_config['private_docker_registry'] == 'registry.lain.local'


def test_lain_user_conf_user_smoke(tmpdir):
    user_p = tmpdir.mkdir("user1")
    user_config = LainUserConfig(user_p.strpath + "/.lain")
    domain = {'domain': 'lain.local'}
    user_config.set_config(local=domain)
    _config = user_config.get_config()
    assert _config['local']['domain'] == 'lain.local'
