#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml


LAIN_USER_CONFIG_FILE_NAME = "lain.conf.yaml"
LAIN_USER_GLOBAL_CONFIG_FILE_NAME = "global.conf.yaml"
LAIN_USER_CONFIG_PATH = os.path.expanduser("~/.lain")
LAIN_GLOBAL_CONFIG_FILE_NAME = "lain.conf.yaml"
LAIN_GLOBAL_CONFIG_PATH = "/etc/lain"

LAIN_CONFIG_SSO_URL_KEY = "sso_url"
LAIN_CONFIG_SSO_TOKEN_KEY = "sso_token"
LAIN_CONFIG_SSO_REFRESH_TOKEN_KEY = "sso_refresh_token"
LAIN_CONFIG_DOMAIN_KEY = "domain"


class LainUserConfig:

    global_config_file = os.path.join(
        LAIN_GLOBAL_CONFIG_PATH, LAIN_GLOBAL_CONFIG_FILE_NAME)
    sso_url_key = LAIN_CONFIG_SSO_URL_KEY
    sso_token_key = LAIN_CONFIG_SSO_TOKEN_KEY
    sso_refresh_token_key = LAIN_CONFIG_SSO_REFRESH_TOKEN_KEY
    domain_key = LAIN_CONFIG_DOMAIN_KEY

    @classmethod
    def get_config_from(cls, config_file):
        try:
            with open(config_file) as f:
                lain_config = yaml.safe_load(f.read())
            return lain_config if lain_config else {}
        except Exception:
            return {}

    @classmethod
    def create(cls, config_path=None):
        _path = config_path if config_path else LAIN_USER_CONFIG_PATH
        return LainUserConfig(_path)

    def __init__(self, config_path):
        self.config_path = config_path
        self.user_config_file = os.path.join(
            config_path, LAIN_USER_CONFIG_FILE_NAME)
        self.user_global_config_file = os.path.join(
            config_path, LAIN_USER_GLOBAL_CONFIG_FILE_NAME)

    def ensure_config_path(self):
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)

    def set_config(self, **kwargs):
        _config = self.get_config_from(self.user_config_file)
        for key, values in kwargs.iteritems():
            if not _config.has_key(key):
                _config[key] = {}
            for k, v in values.iteritems():
                _config[key][k] = v
        self.save_config(_config)
        return _config

    def save_config(self, config):
        self.ensure_config_path()
        with open(self.user_config_file, "w") as f:
            f.write(yaml.safe_dump(config, default_flow_style=False))

    def set_global_config(self, **kwargs):
        _config = self.get_config_from(self.user_global_config_file)
        for key, value in kwargs.iteritems():
            _config[key] = value
        self.save_global_config(_config)
        return _config

    def save_global_config(self, config):
        self.ensure_config_path()
        with open(self.user_global_config_file, "w") as f:
            f.write(yaml.safe_dump(config, default_flow_style=False))

    def get_config(self):
        _config = LainUserConfig.get_config_from(
            LainUserConfig.global_config_file)
        user_global_config = self.get_config_from(self.user_global_config_file)
        for k, v in user_global_config.iteritems():
            _config[k] = v
        user_config = self.get_config_from(self.user_config_file)
        for k, v in user_config.iteritems():
            _config[k] = v
        return _config

    def get_available_phases(self):
        phases = []
        user_config = self.get_config_from(self.user_config_file)
        for k, _ in user_config.iteritems():
            phases.append(k)
        return phases
