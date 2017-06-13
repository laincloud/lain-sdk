#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import copy
from sys import stderr
import errno
import subprocess
import shutil
import requests
from requests.auth import HTTPBasicAuth
from .yaml.conf import user_config
from docker import auth


# copied from HongQN
def _colorize(code):
    def _(text, bold=False):
        c = code
        if bold:
            c = '1;%s' % c
        return '\033[%sm%s\033[0m' % (c, text)
    return _

_red = _colorize('31')
_green = _colorize('32')
_yellow = _colorize('33')


def info(msg):
    print(_green(">>> " + msg))


def error(msg):
    print(_red(">>> " + msg, True))


def warn(msg):
    print(_yellow(">>> " + msg, True))


# Log
logging.basicConfig(
    # filename=os.path.join("log", time.asctime().replace(':',' ').replace(' ', '_')),
    level=logging.DEBUG,
    #format='(%(process)d-%(threadName)s) [%(asctime)s] [%(levelname)s] [%(pathname)s:%(funcName)s:%(lineno)d]  %(message)s',
    format='[%(levelname)s] %(message)s %(pathname)s:%(funcName)s:%(lineno)d',
    datefmt='%m/%d/%Y %I:%M:%S %p')
log = logging


def recur_create_file(path):
    if os.path.exists(path):
        print >> stderr, "Error: {} already exists".format(path)
        exit(1)
    par_dir = os.path.dirname(path)
    if not os.path.exists(par_dir):
        os.makedirs(par_dir)
    open(path, 'a').close()


def file_parent_dir(path):
    return os.path.dirname(os.path.abspath(path))


def get_cfd(file):
    return file_parent_dir(file)


def touch(path):
    """like `touch` in `bash`

    If `path` is already a file, content will be removed
    """

    open(path, 'w').close()


def rm(path):
    """Deletes files or directories."""

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def mkdir_p(path):
    """mkdir -p"""

    try:
        os.makedirs(path)
    except OSError as e:
        if not e.errno == errno.EEXIST:
            raise


def meta_version(repo_dir, sha1=''):
    if sha1:
        git_cmd = ['git', 'log', '-1', sha1, '--pretty=format:%ct-%H']
    else:
        git_cmd = ['git', 'log', '-1', '--pretty=format:%ct-%H']

    try:
        commit_hash = subprocess.check_output(
            git_cmd, cwd=repo_dir, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        warn('Error getting cd Git commit hash: {}'.format(e.output))
        return None

    return commit_hash


REGISTRY_CONNECT_TIMEOUT = 3
REGISTRY_READ_TIMEOUT = 5


def parse_registry_auth(registry):
    need_auth, auth_url = False, ''
    registry_url = "http://%s/v2" % registry
    try:
        r = requests.get(registry_url, timeout=(
            REGISTRY_CONNECT_TIMEOUT, REGISTRY_READ_TIMEOUT))
        need_auth = r.status_code == 401
        if need_auth:
            auth_url = _get_registry_auth_url(r)
        return need_auth, auth_url
    except Exception:
        warn("can not access registry : %s" % registry)
        return False, ''


# auth header example:
# WWW-Authenticate: Bearer realm="url",Service="domain"
def _get_registry_auth_url(response):
    try:
        auth_header = response.headers['WWW-Authenticate']
        params = auth_header.split(',')
        auth_url = params[0].split('=')[1]
        return auth_url[1:len(auth_url) - 1]
    except Exception as e:
        error("parse registry auth url failed: %s" % str(e))
        return ''


def get_jwt_for_registry(auth_url, registry, appname):
    # get auth username and password from dockercfg
    try:
        cfg = auth.resolve_authconfig(auth.load_config(), registry=registry)
        username = cfg['username'] if 'username' in cfg else cfg['Username']
        password = cfg['password'] if 'password' in cfg else cfg['Password']
        # phase, phase_config = get_phase_config_from_registry(registry)
        # domain = phase_config.get(user_config.domain_key, '')
        # only use `lain.local` as service
        url = "%s?service=%s&scope=repository:%s:push,pull&account=%s" % (
            auth_url, "lain.local", appname, username)
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        if response.status_code < 400 and response.json()['token']:
            return response.json()['token']
    except Exception as e:
        warn("can not load registry auth config : %s, need lain login first." % e)
        return ''


def lain_based_path(path, base='/lain/app'):
    return os.path.normpath(os.path.join(base, path))


def get_phase_config_from_registry(registry):
    etc = user_config.get_config()
    for k, v in etc.iteritems():
        if isinstance(v, dict):
            if registry == "registry.{}".format(v.get('domain', '')):
                return k, copy.deepcopy(v)
    return None, None
