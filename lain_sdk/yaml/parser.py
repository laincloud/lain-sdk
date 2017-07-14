#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import yaml
from jinja2 import Template
import json
import copy
import os
from enum import Enum
from os.path import abspath

from ..mydocker import gen_image_name
from .conf import PRIVATE_REGISTRY, DOMAIN, DOCKER_APP_ROOT
from ..util import lain_based_path

SOCKET_TYPES = 'tcp udp'
SocketType = Enum('SocketType', SOCKET_TYPES)
PROC_TYPES = 'worker web oneshot portal'
ProcType = Enum('ProcType', PROC_TYPES)
CloudVolumeType = ['multi', 'single']
DEFAULT_SYSTEM_VOLUMES = [
    "/data/lain/entrypoint:/lain/entrypoint:ro", "/etc/localtime:/etc/localtime:ro"]
VALID_PREPARE_VERSION_PATERN = re.compile(r'^[a-zA-Z0-9]+$')
INVALID_APPNAMES = ('service', 'resource', 'portal')
INVALID_VOLUMES = ('/', '/lain', DOCKER_APP_ROOT)
MIN_SETUP_TIME = 0
MAX_SETUP_TIME = 120
MIN_KILL_TIMEOUT = 10
MAX_KILL_TIMEOUT = 60


def restrict_value(v, minv, maxv):
    if v < minv:
        return minv
    elif v > maxv:
        return maxv
    return v


def is_section(keyword, section_class):
    _keyword = keyword.split('.')[0]
    if _keyword in section_class.SECTION_KEYWORDS._member_names_:
        return True
    return False


def just_simple_scale(keyword, scale_class):
    if keyword in scale_class.SIMPLE_SCALE_KEYWORDS._member_names_:
        return True
    return False


def split_path(path):
    pathlist = []
    while 1:
        tmp = os.path.split(path)
        pathlist.append(tmp[1])
        if tmp[0] == '/':
            pathlist.append('/')
            break
        path = tmp[0]
    pathlist.reverse()
    return pathlist


def simplify_path(pathlist):
    plist = []
    for item in pathlist:
        if item == '..':
            if len(plist) > 1:
                plist.pop()
        else:
            plist.append(item)
    return plist


def join_path(pathlist):
    first = pathlist[0]
    for item in pathlist[1:]:
        first = os.path.join(first, item)
    return first


def parse_path(paths):
    ret = []
    for item in paths:
        ret.append(join_path(simplify_path(split_path(os.path.join(DOCKER_APP_ROOT,
                                                                   item)))))
    return ret


def validate_volume(path):
    _path = os.path.join(DOCKER_APP_ROOT, path.strip())
    return not abspath(_path) in INVALID_VOLUMES


class Labels:
    SECTION_KEYWORDS = Enum('SECTION_KEYWORDS', 'labels')
    patten = re.compile(r'(.*):(.*)')

    def load(self, meta):
        self.labels = {}
        if isinstance(meta, str):
            key, value = self.parse(meta)
            self.labels[key] = value
        elif isinstance(meta, list):
            for m in meta:
                key, value = self.parse(m)
                self.labels[key] = value

    def parse(self, meta):
        m = self.patten.match(meta)
        if m:
            return m.group(1), m.group(2)
        raise Exception('not supported labels desc %s' % (meta, ))


class Filters:
    SECTION_KEYWORDS = Enum('SECTION_KEYWORDS', 'filters')
    patten = re.compile(r'(affinity|constraint):(.*)(==|!=)(.*)')

    def load(self, meta):
        self.filters = []
        if isinstance(meta, str):
            self.parse(meta)
            self.filters.append(meta)
        elif isinstance(meta, list):
            for m in meta:
                self.parse(m)
                self.filters.append(m)

    def parse(self, meta):
        m = self.patten.match(meta)
        if m:
            return meta
        raise Exception('not supported labels desc %s' % (meta, ))


class Ports:
    SECTION_KEYWORDS = Enum('SECTION_KEYWORDS', 'ports')
    MAX_PORT = 10000
    MIN_PORT = 9500

    def load(self, meta):
        self.ports = []
        self.src_port = []
        if isinstance(meta, str):
            src_port, dst_port, proto = self.parse(m)
            port_mapping = {'srcport': src_port,
                            'dstport': dst_port, 'proto': proto}
            self.ports = [port_mapping]
        elif isinstance(meta, dict):
            for m, v in meta.items():
                src_port, dst_port, proto = self.parse(m)
                port_mapping = {'srcport': src_port,
                                'dstport': dst_port, 'proto': proto}
                if isinstance(v, dict):
                    port_mapping.update(v)
                self.ports.append(port_mapping)

    def parse(self, meta):
        if isinstance(meta, int):
            meta = str(meta)
        values = meta.split('/')
        proto = SocketType.tcp.name
        if len(values) == 2 and (values[1] == SocketType.udp.name or values[1] == SocketType.tcp.name):
            proto = values[1]
        ports_mapping = values[0]
        ports = ports_mapping.split(':')
        if len(ports) >= 2:
            src_port = ports[0]
            dst_port = ports[1]
        elif len(ports) == 1:
            src_port = dst_port = ports[0]
        else:
            raise Exception('not supported ports desc %s' % (meta, ))
        src_port = self.valid_port(src_port)
        if src_port < self.MIN_PORT or src_port > self.MAX_PORT:
            raise Exception('src port should between %s and %s' %
                            (self.MIN_PORT, self.MAX_PORT))
        if src_port in self.src_port:
            raise Exception('cant bind src port to many dst ports %s' %
                            (meta, ))
        self.src_port.append(src_port)
        dst_port = self.valid_port(dst_port)
        if dst_port < 1 or dst_port > 65535:
            raise Exception('dst port should between %s and %s' % (1, 65535))
        return src_port, dst_port, proto

    def valid_port(self, portstr):
        try:
            port = int(portstr)
        except ValueError:
            raise Exception('not supported ports desc %s' % (portstr, ))
        return port


class Port:
    SECTION_KEYWORDS = Enum('SECTION_KEYWORDS', 'port')
    port = 80
    type = SocketType.tcp

    def load(self, meta):
        '''
        meta maybe:
            80
            '80:tcp'
            {80: ['type:tcp']}
        '''
        if isinstance(meta, int):
            self.port = meta
            self.type = SocketType.tcp
        elif isinstance(meta, str):
            port_info = meta.split(':')
            if len(port_info) == 2:
                self.port = int(port_info[0])
                self.type = SocketType[port_info[1]]
            else:
                raise Exception('not supported port desc %s' % (meta, ))
        elif isinstance(meta, dict):
            self.port = meta.keys()[0]
            _pi = meta.values()[0][0].split(':')
            assert _pi[0] == 'type'
            self.type = SocketType[_pi[1]]
        else:
            raise Exception('not supported port desc %s' % (meta, ))


class Proc:
    SECTION_KEYWORDS = Enum('SECTION_KEYWORDS', PROC_TYPES + " proc service")
    SIMPLE_SCALE_KEYWORDS = Enum(
        "SIMPLE_SCALE_KEYWORDS", "num_instances cpu memory")
    name = ''
    type = ProcType.worker
    image = ''
    entrypoint = ''
    cmd = ''
    num_instances = 1
    cpu = 0
    memory = '32m'
    port = {}
    ports = []
    mountpoint = []
    https_only = True
    healthcheck = ''
    container_healthcheck = {}
    user = ''
    working_dir = ''
    dns_search = []
    env = []
    volumes = []
    system_volumes = []
    cloud_volumes = {}
    secret_files = []  # for proc
    secret_files_bypass = False
    service_name = ''
    allow_clients = ''
    backup = []
    logs = []
    stateful = False
    setup_time = 0
    kill_timeout = 10

    def load(self, keyword, meta, appname, meta_version, default_image, **cluster_config):
        default_image_name = default_image or gen_image_name(
            appname,
            'release',
            meta_version=meta_version,
            docker_reg=cluster_config.get('registry', PRIVATE_REGISTRY)
        )
        proc_info = keyword.split('.')
        if len(proc_info) == 2:
            self.name = proc_info[1]
            if proc_info[0] in PROC_TYPES.split():
                self.type = ProcType[proc_info[0]]  # 放弃meta里面的type定义
            else:
                self.type = ProcType[meta.get('type', 'worker')]
        if len(proc_info) == 1:
            self.name = proc_info[0]
            self.type = ProcType[proc_info[0]]  # 放弃meta里面的type定义
        self.image = meta.get('image', default_image_name)
        meta_entrypoint = meta.get('entrypoint')
        self.entrypoint = self.__to_exec_form(meta_entrypoint)
        meta_cmd = meta.get('cmd')
        self.cmd = self.__to_exec_form(meta_cmd)
        self.user = meta.get('user', '')
        self.working_dir = meta.get('workdir') or meta.get('working_dir', '')
        dns_search_meta = meta.get('dns_search', [])
        app_dns_search = "%s.lain" % get_app_domain(appname)
        if app_dns_search not in dns_search_meta:
            dns_search_meta.append(app_dns_search)
        self.dns_search = dns_search_meta
        self.cpu = meta.get('cpu', 0)
        self.memory = meta.get('memory', '32m')
        self.num_instances = meta.get('num_instances', 1)
        port_meta = meta.get('port', None)
        if port_meta:
            self.port = self._load_ports(port_meta)
        else:
            if self.type == ProcType.web:
                _port = Port()
                self.port = {_port.port: _port}
        ports_meta = meta.get('ports', None)
        self.ports = []
        self.labels = {}
        self.filters = []
        if ports_meta:
            self.ports = self._load_ports_mapping(ports_meta)
        labels_meta = meta.get('labels', None)
        if labels_meta:
            self.labels = self._load_labels(labels_meta)
        filters_meta = meta.get('filters', None)
        if filters_meta:
            self.filters = self._load_filters(filters_meta)

        stateful_meta = meta.get('stateful', False)
        if stateful_meta:
            self.stateful = True
        else:
            self.stateful = False

        self.setup_time = restrict_value(
            meta.get('setup_time', 0), MIN_SETUP_TIME, MAX_SETUP_TIME)
        self.kill_timeout = restrict_value(
            meta.get('kill_timeout', 10), MIN_KILL_TIMEOUT, MAX_KILL_TIMEOUT)

        # TODO 检验mountpoint段是否合法
        # ProcType.web 的 proc 有 mountpoint
        if self.type == ProcType.web:
            mountpoint_meta = meta.get('mountpoint', None)
            # TODO: change to "True" in near-future
            self.https_only = meta.get('https_only', False)
            app_domain = get_app_domain(appname)
            domains = cluster_config.get('domains', [DOMAIN])

            # 默认注入的 mountpoint 包括
            # - [APPDOMAIN.domain for domain in domains]
            # - APPDOMAIN.lain
            default_mountpoints = []
            for d in domains:
                default_mountpoints.append("%s.%s" % (app_domain, d))
            default_mountpoints.append("%s.lain" % (app_domain, ))

            if self.name == 'web':
                # ProcName == 'web' 则自动插入 default_mountpoints
                # - APPNAME.CLUSTER_DOMAIN
                # - APPNAME.lain
                if not mountpoint_meta or not isinstance(mountpoint_meta, list):
                    self.mountpoint = default_mountpoints
                else:
                    for mp in default_mountpoints:
                        if mp not in mountpoint_meta:
                            mountpoint_meta.append(mp)
                    self.mountpoint = mountpoint_meta
            else:
                # ProcName != 'web' 则必须有另外的 mountpoint
                if not mountpoint_meta or not isinstance(mountpoint_meta, list):
                    raise Exception(
                        'proc (type is web but name is not web) should have own mountpoint.\nkeyword: %s\nmeta: %s' % (keyword, meta))
                else:
                    self.mountpoint = mountpoint_meta
            to_remove = []
            for mp in self.mountpoint:
                if mp.startswith('/'):
                    to_remove.append(mp)
                    if len(mp) > 1:
                        for dmp in default_mountpoints:
                            self.mountpoint.append("%s%s" % (dmp, mp))
            for mp in to_remove:
                self.mountpoint.remove(mp)

        # ProcType.web 的 proc 可以有 healthcheck
        if self.type == ProcType.web:
            healthcheck_meta = meta.get('healthcheck', None)
            self.healthcheck = healthcheck_meta if healthcheck_meta else ''

        self.container_healthcheck = meta.get('container_healthcheck', None)
        # TODO 检验env段是否合法
        # - 是否是list
        self.env = meta.get('env') or self.env

        self.volumes, self.backup = [], []
        for volume in meta.get('persistent_dirs') or meta.get('volumes') or []:
            if isinstance(volume, str):
                self.volumes.append(lain_based_path(volume))
            elif isinstance(volume, dict):
                if len(volume) == 0:
                    continue
                key = volume.keys()[0]  # there's only one key in this dict

                for attr, setting in volume[key].iteritems():
                    if attr == "backup_full" or attr == "backup_increment":
                        schedule, expire = setting.get(
                            'schedule', ""), setting.get('expire', "")
                        if schedule == "":
                            continue
                        self.backup.append({
                            'procname': "%s.%s.%s" % (appname, self.type.name, self.name),
                            'volume': key,
                            'schedule': schedule,
                            'expire': expire,
                            'mode': 'increment' if attr == "backup_increment" else "full",
                            'preRun': setting.get('pre_run', ""),
                            'postRun': setting.get('post_run', ""),
                        }
                        )
                self.volumes.append(lain_based_path(key))
        for volume in self.volumes:
            if not validate_volume(volume):
                raise Exception('invalid volume: abs volume {} should not in {}'.format(
                    volume, INVALID_VOLUMES))

        self.logs = []
        logs_meta = meta.get('logs', [])
        for log in logs_meta:
            if log.startswith('/'):
                raise Exception(
                    "Log in Logs section MUST be a relative path based on /lain/logs. Wrong path: %s" % (log))
            if log not in self.logs:
                self.logs.append(log)
        if logs_meta:
            self.volumes.append('/lain/logs')

        # add default system volume
        self.system_volumes = DEFAULT_SYSTEM_VOLUMES

        self.cloud_volumes = self._load_cloud_volumes(meta)

        # for secret_files
        self.secret_files = meta.get('secret_files') or []
        # add /lain/app for relative paths
        self.secret_files = parse_path(self.secret_files)
        self.secret_files_bypass = meta.get('secret_files_bypass') or False

        # ProcType.portal 的 proc 有 service_name 和 allow_clients
        if self.type == ProcType.portal:
            service_name_meta = meta.get('service_name', None)
            if service_name_meta is None:
                raise Exception(
                    'proc (type is portal) should have own service_name.\nkeyword: %s\nmeta: %s' % (keyword, meta))
            allow_clients_meta = meta.get('allow_clients', "**")
            self.service_name = service_name_meta
            self.allow_clients = allow_clients_meta

    def _load_cloud_volumes(self, meta):
        cloud_volumes = {}
        vol_info = meta.get('cloud_volumes', None)
        if vol_info:
            vol_type = vol_info.get('type', 'multi')
            if vol_type not in CloudVolumeType:
                raise Exception(
                    "cloud volume type %s not supported, only multi and single are valid" % vol_type)
            vol_dirs = []
            for vol in vol_info.get('dirs') or []:
                vol_dirs.append(lain_based_path(vol))
            cloud_volumes[vol_type] = vol_dirs
        return cloud_volumes

    def _load_ports(self, meta):
        if not isinstance(meta, list):
            meta = [meta]
        _port = {}
        for m in meta:
            if isinstance(m, int) or isinstance(m, str) or isinstance(m, dict):
                p = Port()
                p.load(m)
                _port[p.port] = p
            else:
                raise Exception('not supported port desc: %s' % (m, ))
        return _port

    def _load_ports_mapping(self, meta):
        ps = Ports()
        ps.load(meta)
        return ps.ports

    def _load_labels(self, meta):
        lbs = Labels()
        lbs.load(meta)
        return lbs.labels

    def _load_filters(self, meta):
        flts = Filters()
        flts.load(meta)
        return flts.filters

    def patch(self, payload):
        # 这里仅限于proc自身信息的变化，不可包括meta_version
        self.entrypoint = payload.get('entrypoint', self.entrypoint)
        meta_cmd = payload.get('cmd', self.cmd)
        self.cmd = self.__to_exec_form(meta_cmd)
        self.cpu = payload.get('cpu', self.cpu)
        self.memory = payload.get('memory', self.memory)
        self.num_instances = payload.get('num_instances', self.num_instances)
        port_meta = payload.get('port', None)
        if port_meta:
            # TODO 支持multi port
            self.port = self._load_ports(port_meta)

    def patch_only_simple_scale_meta(self, proc):
        # 仅patch此proc的动态scale的meta信息
        for k in self.SIMPLE_SCALE_KEYWORDS._member_names_:
            self.__dict__[k] = proc.__dict__[k]

    def __to_exec_form(self, command_and_params):
        """ 将 shell form(空格分隔) 转变为 exec form(string list)，或者保持 exec form 的格式
        """
        if isinstance(command_and_params, basestring):
            command_and_params_list = command_and_params.split()
        elif isinstance(command_and_params, list) and all(isinstance(item, basestring) for item in command_and_params):
            command_and_params_list = command_and_params
        else:   # None 或者非法输入，如果是非法输入，在 lain build 时会给出警告
            command_and_params_list = []
        return command_and_params_list

    @property
    def annotation(self):
        data = {}
        if self.mountpoint is not None:
            data['mountpoint'] = self.mountpoint
        if self.https_only is not None:
            data['https_only'] = self.https_only
        if self.service_name:
            data['service_name'] = self.service_name
        if self.backup:
            data['backup'] = self.backup
        if self.healthcheck:
            data['healthcheck'] = self.healthcheck
        if self.logs:
            data['logs'] = self.logs
        if self.ports:
            data['ports'] = self.ports
        return json.dumps(data)


class Prepare:
    version = "0"
    script = []
    keep = []

    def load(self, meta):
        if isinstance(meta, list):
            self.version = "0"
            self.script = meta
            self.script = ['( %s )' % s for s in self.script]
            self.keep = []
        else:
            version = str(meta.get('version', '0')).strip()
            if VALID_PREPARE_VERSION_PATERN.match(version):
                self.version = version
            else:
                raise Exception(
                    "invalid prepare version: %s\nVALID_PREPARE_VERSION_PATERN: r\"^[a-zA-Z0-9]+$\"" % version)
            self.script = meta.get('script') or []
            self.script = ['( %s )' % s for s in self.script]
            self.keep = meta.get('keep') or self.keep
            self.build_arg = meta.get('build_arg') or []
        keep_script = ""
        for k in self.keep:
            keep_script += '| grep -v \'\\b%s\\b\' ' % k
        clean_script = "( ls -1 %s| xargs rm -rf )" % keep_script
        self.script.append(clean_script)


class Build:
    base = ''
    prepare = None
    script = []

    def load(self, meta):
        base = meta.get('base', None)
        if base is None:
            raise Exception('no base in section build')
        self.script = meta.get('script') or []
        self.script = ['( %s )' % s for s in self.script]
        self.build_arg = meta.get('build_arg') or []
        self.base = base
        prepare = meta.get('prepare', {})
        self.prepare = Prepare()
        self.prepare.load(prepare)


class Release:
    script = []
    dest_base = ''
    copy = []

    def load(self, meta):
        self.script = meta.get('script') or []
        self.script = ['( %s )' % s for s in self.script]
        self.dest_base = meta.get('dest_base') or self.dest_base
        copy_meta = meta.get('copy') or []
        self.copy = []
        for c in copy_meta:
            if isinstance(c, str):
                self.copy.append({
                    'src': c,
                    'dest': c
                })
            elif isinstance(c, dict):
                self.copy.append(c)
            else:
                pass


class Test:
    script = []

    def load(self, meta):
        self.script = meta.get('script') or []
        self.script = ['( %s )' % s for s in self.script]


class LainConf:
    appname = ''
    giturl = ''
    build = Build()
    release = Release()
    test = Test()
    procs = {}
    notify = {}
    use_services = {}
    use_resources = {}

    def load(self, meta_yaml, meta_version, default_image, **cluster_config):
        meta = yaml.safe_load(meta_yaml)
        self.meta_version = meta_version
        self.appname = meta.get('appname', None)
        self.giturl = meta.get('giturl', None)
        if self.appname is None:
            raise Exception('invalid lain conf: no appname')
        if self.appname in INVALID_APPNAMES:
            raise Exception('invalid lain conf: appname {} should not in {}'.format(
                self.appname, INVALID_APPNAMES))
        self.procs = self._load_procs(meta, self.appname, meta_version, default_image, registry=cluster_config.get(
            'registry', PRIVATE_REGISTRY), domains=cluster_config.get('domains', [DOMAIN]))
        self.build = self._load_build(meta)
        self.release = self._load_release(meta)
        self.test = self._load_test(meta)
        self.notify = self._load_notify(meta)

        use_services_meta = meta.get('use_services', None)
        if use_services_meta:
            self.use_services = self._load_use_services(use_services_meta)

        use_resources_meta = meta.get('use_resources', None)
        if use_resources_meta:
            self.use_resources = self._load_use_resources(use_resources_meta)

    def _load_procs(self, meta, appname, meta_version, default_image, **cluster_config):
        _procs = {}

        def _proc_load(key, meta, **cluster_config):
            _proc = Proc()
            _proc.load(key, meta, appname, meta_version, default_image, registry=cluster_config.get(
                'registry', PRIVATE_REGISTRY), domains=cluster_config.get('domains', [DOMAIN]))

            # TODO 更多错误校验
            if _proc.name in _procs.keys():
                raise Exception("duplicated proc name %s" % (_proc.name, ))
            _procs[_proc.name] = _proc
        for key in meta.keys():
            if not is_section(key, Proc):
                continue
            if key.startswith("service."):
                _key = key.split(".")
                if len(_key) > 2 or _key[1] == "":
                    raise Exception("invalid service keyword: %s" % key)

                _service_worker_key = "proc.%s" % _key[1]
                _service_worker_meta = copy.deepcopy(meta[key])
                _service_portal_key = "portal.portal-%s" % _key[1]
                _service_portal_meta = _service_worker_meta.pop('portal')
                _service_portal_meta['service_name'] = _key[1]

                _proc_load(_service_worker_key,
                           _service_worker_meta, **cluster_config)
                _proc_load(_service_portal_key,
                           _service_portal_meta, **cluster_config)
            else:
                _proc_load(key, meta[key], **cluster_config)
        return _procs

    def _load_use_services(self, meta):
        if isinstance(meta, dict):
            return meta
        else:
            return {}

    def _load_use_resources(self, meta):
        if isinstance(meta, dict):
            use_resources = {}
            try:
                for k, v in meta.iteritems():
                    tmp_v = copy.deepcopy(v)
                    use_resources[k] = {'services': tmp_v.pop('services')}
                    use_resources[k]['context'] = tmp_v
            except Exception:
                raise Exception("invalid resource defination: %s" % meta)
            return use_resources
        else:
            return {}

    def _load_build(self, meta):
        meta = meta.get('build', None)
        if meta is None:
            raise Exception("no build section in lain.yaml")
        self.build.load(meta)
        return self.build

    def _load_release(self, meta):
        meta = meta.get('release', None)
        if meta is not None:
            self.release.load(meta)
        return self.release

    def _load_test(self, meta):
        meta = meta.get('test', None)
        if meta is not None:
            self.test.load(meta)
        return self.test

    def _load_notify(self, meta):
        meta = meta.get('notify', None)
        if meta is not None:
            return meta
        return {}


def get_app_domain(appname):
    try:
        app_domain_list = appname.split('.')
        app_domain_list.reverse()
        app_domain = '.'.join(app_domain_list)
    except Exception:
        app_domain = appname
    return app_domain


def resource_instance_name(resource_appname, client_appname):
    return "resource.{}.{}".format(resource_appname, client_appname)


def render_resource_instance_meta(
        resource_appname, resource_meta_version, resource_meta_template,
        client_appname, context, registry, domains):
    # 用 use_resources 里的变量渲染 resource 模板
    instance_yaml = render_instance_yaml(resource_meta_template, context)
    instance_meta = yaml.dump(instance_yaml, default_flow_style=False)
    resource_config = LainConf()
    resource_config.load(
        instance_meta, resource_meta_version, None,
        registry=registry, domains=domains
    )
    # 将 appname 替换成 resource instance appname
    instance_appname = resource_instance_name(resource_appname, client_appname)
    instance_yaml['appname'] = instance_appname
    # 将 apptype 的 key 删除
    instance_yaml.pop('apptype', None)
    # return 最终的 yaml dump
    return yaml.dump(instance_yaml, default_flow_style=False)


def render_instance_yaml(resource_meta_template, context):
    instance_yaml = yaml.safe_load(resource_meta_template)
    for key in instance_yaml:
        if type(instance_yaml[key]) == dict:
            iterate_parse_yaml_dict(instance_yaml[key], context)
        elif type(instance_yaml[key]) == list:
            iterate_parse_yaml_list(instance_yaml[key], context)
        else:
            instance_yaml[key] = get_jinja_render_value(
                instance_yaml[key], context)
    return instance_yaml


def iterate_parse_yaml_dict(dict_yaml, context):
    for key in dict_yaml:
        if type(dict_yaml[key]) == dict:
            iterate_parse_yaml_dict(dict_yaml[key], context)
        elif type(dict_yaml[key]) == list:
            iterate_parse_yaml_list(dict_yaml[key], context)
        else:
            dict_yaml[key] = get_jinja_render_value(dict_yaml[key], context)


def iterate_parse_yaml_list(list_yaml, context):
    for index in range(len(list_yaml)):
        if type(list_yaml[index]) == list:
            iterate_parse_yaml_list(list_yaml[index], context)
        elif type(list_yaml[index]) == dict:
            iterate_parse_yaml_dict(list_yaml[index], context)
        else:
            list_yaml[index] = get_jinja_render_value(
                list_yaml[index], context)


def get_jinja_render_value(value, context):
    template = Template(str(value))
    update_value = str(template.render(**context))
    try:
        update_value = int(update_value)
    except Exception:
        pass
    return update_value
