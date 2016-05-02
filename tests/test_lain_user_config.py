# -*- coding: utf-8

import pytest
from lain_sdk.yaml.lain_user_config import LainUserConfig


@pytest.fixture
def patch_lain_user_config_base(tmpdir, monkeypatch):
    base_p = tmpdir.mkdir("etc").mkdir("lain")
    base_f = base_p.join("lain.conf.yaml")
    base_f.write("mirror_registry: docker.bdp.cc:5000\nprivate_docker_registry: registry.lain.local")
    monkeypatch.setattr(LainUserConfig, 'config_path', base_p.strpath)
    monkeypatch.setattr(LainUserConfig, 'config_file', base_f.strpath)

def test_lain_user_conf_base_empty_smoke(tmpdir):
    etc_path = tmpdir.mkdir("etc").mkdir("lain")
    print etc_path.strpath
    assert LainUserConfig.get_config_from(etc_path.strpath) == {}

def test_lain_user_conf_base_smoke(tmpdir):
    p = tmpdir.mkdir("etc").mkdir("lain").join("lain.conf.yaml")
    p.write("mirror_registry: docker.bdp.cc:5000\nprivate_docker_registry: registry.lain.local")
    p_config = LainUserConfig.get_config_from(p.strpath)
    assert p_config['mirror_registry'] == 'docker.bdp.cc:5000'
    assert p_config['private_docker_registry'] == 'registry.lain.local'

@pytest.mark.usefixtures("patch_lain_user_config_base")
def test_lain_user_conf_user_empty_smoke(tmpdir):
    user_p = tmpdir.mkdir("user1")
    user_config = LainUserConfig.create(user_p.strpath)
    _config = user_config.get_config()
    assert _config['mirror_registry'] == 'docker.bdp.cc:5000'
    assert _config['private_docker_registry'] == 'registry.lain.local'

@pytest.mark.usefixtures("patch_lain_user_config_base")
def test_lain_user_conf_user_smoke(tmpdir):
    user_p = tmpdir.mkdir("user1")
    user_config = LainUserConfig(user_p.strpath + "/.lain")
    domain = {'domain': 'lain.local'}
    user_config.set_config(local=domain)
    _config = user_config.get_config()
    assert _config['local']['domain'] == 'lain.local'
    assert _config['private_docker_registry'] == 'registry.lain.local'