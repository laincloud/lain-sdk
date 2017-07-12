# -*- coding: utf-8 -*-

import json
import yaml
import pytest
from unittest import TestCase
from lain_sdk.yaml.parser import (
    LainConf, ProcType, Proc,
    just_simple_scale,
    render_resource_instance_meta, DEFAULT_SYSTEM_VOLUMES,
    DOMAIN,
    MIN_SETUP_TIME, MAX_SETUP_TIME, MIN_KILL_TIMEOUT, MAX_KILL_TIMEOUT
)

FIXTURES_EXTRA_DOMAINS = ['extra.domain1.com', 'extra.domain2.org']


class LainConfUtilsTests(TestCase):

    def test_just_simple_scale(self):
        assert just_simple_scale('cpu', Proc)
        assert not just_simple_scale('cmd', Proc)


class LainConfTests(TestCase):

    def test_lain_conf_without_appname(self):
        meta_yaml = '''
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        with pytest.raises(Exception) as e:
            hello_conf.load(meta_yaml, meta_version, None)
            assert 'invalid lain conf: no appname' in str(e.value)

    def test_lain_conf_smoke(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    web.bar:
                        cmd: bar
                        port: 8080
                        mountpoint:
                            - a.com
                            - b.cn/xyz
                        https_only: false
                    worker.foo:
                        cmd: worker
                        memory: 128m
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == ['ENV_A=enva', 'ENV_B=envb']
        assert hello_conf.procs['web'].memory == '64m'
        assert hello_conf.procs['web'].user == ''
        assert hello_conf.procs['web'].working_dir == ''
        assert hello_conf.procs['web'].dns_search == ['hello.lain']
        assert hello_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert hello_conf.procs['web'].port[80].port == 80
        assert hello_conf.procs['web'].stateful is False
        assert hello_conf.procs['foo'].memory == '128m'
        assert hello_conf.procs['foo'].cmd == ['worker']
        assert hello_conf.procs['foo'].type == ProcType.worker
        assert hello_conf.procs['bar'].cmd == ['bar']
        assert hello_conf.procs['bar'].type == ProcType.web
        assert hello_conf.procs['bar'].mountpoint == ['a.com', 'b.cn/xyz']
        assert hello_conf.procs['bar'].https_only is False

    def test_lain_conf_notify_slack(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    web:
                        cmd: hello
                        port: 80
                    notify:
                        slack: "#hello"
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.appname == 'hello'
        assert hello_conf.notify == {'slack': '#hello'}

    def test_lain_conf_notify_missing(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    web:
                        cmd: hello
                        port: 80
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.appname == 'hello'
        assert hello_conf.notify == {}

    def test_lain_conf_empty_cmd(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd:
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].port[80].port == 80
        assert hello_conf.procs['web'].cmd == []

    def test_lain_conf_port_with_type(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80:tcp
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == ['ENV_A=enva', 'ENV_B=envb']
        assert hello_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert hello_conf.procs['web'].logs == []
        assert hello_conf.procs['web'].port[80].port == 80

    def test_lain_conf_without_logs(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                    web:
                        volumes:
                            - /data
                            - /var/lib/mysql
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert hello_conf.procs['web'].logs == []

    def test_lain_conf_logs(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                    web:
                        volumes:
                            - /data
                            - /var/lib/mysql
                        logs:
                            - a.log
                            - b.log
                            - a.log
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].volumes == [
            '/data', '/var/lib/mysql', '/lain/logs']
        assert hello_conf.procs['web'].logs == ['a.log', 'b.log']
        annotation = json.loads(hello_conf.procs['web'].annotation)
        assert annotation['logs'] == ['a.log', 'b.log']

    def test_lain_conf_port_with_type_but_toomuch(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80:tcp:foo
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        with pytest.raises(Exception) as e:
            hello_conf.load(meta_yaml, meta_version, None)
        assert 'not supported port desc 80:tcp:foo' in str(e.value)

    def test_lain_conf_port_with_type_in_property_list(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: {80: ['type:tcp']}
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == ['ENV_A=enva', 'ENV_B=envb']
        assert hello_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert hello_conf.procs['web'].port[80].port == 80

    def test_lain_conf_port_webtype_without_port_meta(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == ['ENV_A=enva', 'ENV_B=envb']
        assert hello_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert hello_conf.procs['web'].port[80].port == 80

    def test_lain_conf_proc_name(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        script: [go build -o hello]
                    release:
                        dest_base: ubuntu
                        copy:
                            - {dest: /usr/bin/hello, src: hello}
                    test:
                        script: [go test]
                    web.web1:
                        cmd: hello
                        port: 80
                        cpu: 1
                        mountpoint:
                            - a.foo
                    notify: {slack: '#hello'}
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        self.assertEquals(hello_conf.appname, 'hello')
        self.assertEquals(hello_conf.procs['web1'].cpu, 1)
        self.assertEquals(hello_conf.procs['web1'].port[80].port, 80)

    def test_lain_conf_dup_proc_name(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    proc.web:
                        type: web
                        cmd: hello
                        port: 80
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        with pytest.raises(Exception) as e:
            hello_conf.load(meta_yaml, meta_version, None)
        assert 'duplicated proc name web' in str(e.value)

    def test_lain_conf_proc_type(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        script: [go build -o hello]
                    release:
                        dest_base: ubuntu
                        copy:
                            - {dest: /usr/bin/hello, src: hello}
                    test:
                        script: [go test]
                    proc.mailer: {type: worker, cmd: hello, port: 80, memory: 128m}
                    notify: {slack: '#hello'}
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        self.assertEquals(hello_conf.appname, 'hello')
        self.assertEquals(hello_conf.procs['mailer'].type, ProcType.worker)
        self.assertEquals(hello_conf.procs['mailer'].memory, '128m')
        self.assertEquals(hello_conf.procs['mailer'].port[80].port, 80)

    def test_lain_conf_proc_env_and_volumes_null(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        env:
                        volumes:
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == []
        assert hello_conf.procs['web'].volumes == []
        assert hello_conf.procs['web'].port[80].port == 80

    def test_lain_conf_proc_secret_files(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        secret_files:
                          - "hello/hello.tex"
                          -  " /secret"
                          -     /hello
                    notify:
                        slack: "#hello"
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == []
        assert hello_conf.procs['web'].volumes == []
        assert hello_conf.procs['web'].port[80].port == 80
        assert hello_conf.procs['web'].secret_files_bypass == False
        assert hello_conf.procs['web'].secret_files == [
            '/lain/app/hello/hello.tex', '/lain/app/ /secret', '/hello']

    def test_lain_conf_proc_secret_files_bypass(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        secret_files_bypass: True
                        secret_files:
                          - "hello/hello.tex"
                          -  " /secret"
                          -     /hello
                    notify:
                        slack: "#hello"
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == []
        assert hello_conf.procs['web'].volumes == []
        assert hello_conf.procs['web'].port[80].port == 80
        assert hello_conf.procs['web'].secret_files_bypass == True
        assert hello_conf.procs['web'].secret_files == [
            '/lain/app/hello/hello.tex', '/lain/app/ /secret', '/hello']



    def test_lain_conf_proc_env_notexists(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == []
        assert hello_conf.procs['web'].volumes == []
        assert hello_conf.procs['web'].port[80].port == 80

    def test_lain_conf_proc_patch(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        script: [go build -o hello]
                    release:
                        dest_base: ubuntu
                        copy:
                            - {dest: /usr/bin/hello, src: hello}
                    test:
                        script: [go test]
                    proc.mailer: {type: worker, cmd: hello, port: 80, memory: 128m}
                    notify: {slack: '#hello'}
                    '''
        payload = {
            "cpu": 2,
            "memory": "64m",
            "num_instances": 2,
            "cmd": "hello world",
            "port": 8080
        }
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        mailer = hello_conf.procs['mailer']
        assert mailer.cpu == 0
        assert mailer.memory == "128m"
        assert mailer.num_instances == 1
        assert mailer.cmd == ["hello"]
        assert mailer.port[80].port == 80
        mailer.patch(payload)
        mailer = hello_conf.procs['mailer']
        assert mailer.cpu == 2
        assert mailer.memory == "64m"
        assert mailer.num_instances == 2
        assert mailer.cmd == ["hello", "world"]
        assert mailer.port[8080].port == 8080

    def test_lain_conf_proc_patch_only_simple_scale_meta(self):
        meta_old = {
            "memory": "32m",
            "num_instances": 1,
            "cmd": "hello",
            "port": 80
        }
        meta_new = {
            "cpu": 2,
            "memory": "64m",
            "num_instances": 2,
            "cmd": "hello world",
            "port": 8080
        }
        proc = Proc()
        proc.load('web', meta_old, 'hello',
                  '111111111-aaaaaaaaaaaaaaaaa', None)
        proc1 = Proc()
        proc1.load('web', meta_new, 'hello',
                   '22222222-bbbbbbbbbbbbbbbbb', None)
        assert proc.name == 'web'
        assert proc.type.name == 'web'
        assert proc.cpu == 0
        assert proc.memory == "32m"
        assert proc.cmd == ["hello"]
        assert proc.num_instances == 1
        assert proc.port[80].port == 80
        proc.patch_only_simple_scale_meta(proc1)
        assert proc.name == 'web'
        assert proc.type.name == 'web'
        assert proc.cpu == 2
        assert proc.memory == "64m"
        assert proc.cmd == ["hello"]
        assert proc.num_instances == 2
        assert proc.port[80].port == 80

    def test_lain_conf_auto_insert_default_mountpoint_for_procname_web(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['web'].env == ['ENV_A=enva', 'ENV_B=envb']
        assert hello_conf.procs['web'].memory == '64m'
        assert hello_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert hello_conf.procs['web'].port[80].port == 80
        my_mountpoint = hello_conf.procs['web'].mountpoint
        expect_mountpoint = [
            "%s.%s" % (hello_conf.appname, DOMAIN),
            "%s.lain" % hello_conf.appname,
        ]

        # resource instance test
        resource_instance_meta_yaml = '''
                    appname: resource.demo-service.hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "hello"
                            image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                            cmd: ./proxy
                            port: 4321
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        env:
                            - ENV_A=enva
                            - ENV_B=envb
                        volumes:
                            - /data
                            - /var/lib/mysql
                    notify:
                        slack: "#demo-service"
                    '''
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        domains = [DOMAIN] + FIXTURES_EXTRA_DOMAINS
        r_conf = LainConf()
        r_conf.load(resource_instance_meta_yaml,
                    meta_version, None, domains=domains)
        assert r_conf.appname == 'resource.demo-service.hello'
        assert r_conf.procs['web'].env == ['ENV_A=enva', 'ENV_B=envb']
        assert r_conf.procs['web'].memory == '64m'
        assert r_conf.procs['web'].volumes == ['/data', '/var/lib/mysql']
        assert r_conf.procs['web'].port[80].port == 80
        app_domain = 'hello.demo-service.resource'
        assert r_conf.procs['web'].mountpoint == ["%s.%s" % (app_domain, DOMAIN)] + \
            ["%s.%s" % (app_domain, d) for d in FIXTURES_EXTRA_DOMAINS] + \
            ["%s.lain" % app_domain]

    def test_lain_conf_no_mountpoint_for_not_web_type_proc(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    worker:
                        cmd: worker
                        memory: 64m
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['worker'].memory == '64m'
        assert hello_conf.procs['worker'].mountpoint == []

        # resource instance test
        resource_instance_meta_yaml = '''
                    appname: resource.demo-service.hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "hello"
                            image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                            cmd: ./proxy
                            port: 4321
                    worker:
                        cmd: worker
                        memory: 64m
                    notify:
                        slack: "#demo-service"
                    '''
        repo_name = 'resource.demo-service.hello'
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        r_conf = LainConf()
        r_conf.load(resource_instance_meta_yaml, repo_name, meta_version)
        assert r_conf.appname == 'resource.demo-service.hello'
        assert r_conf.procs['echo'].mountpoint == []
        assert r_conf.procs['worker'].memory == '64m'
        assert r_conf.procs['worker'].mountpoint == []

    def test_lain_conf_auto_prefix_default_mountpoint_for_proctype_web(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        mountpoint:
                            - /web
                            - a.foo
                            - c.com/y/z
                    web.admin:
                        cmd: admin
                        port: 80
                        mountpoint:
                            - /admin
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None, domains=[
                        DOMAIN] + FIXTURES_EXTRA_DOMAINS)
        assert hello_conf.appname == 'hello'
        my_mountpoint = hello_conf.procs['web'].mountpoint
        expect_mountpoint = ['a.foo', 'c.com/y/z',
                             '%s.%s' % (hello_conf.appname, DOMAIN),
                             '%s.lain' % hello_conf.appname,
                             '%s.%s/web' % (hello_conf.appname, DOMAIN),
                             '%s.lain/web' % hello_conf.appname
                             ]
        for extra_domain in FIXTURES_EXTRA_DOMAINS:
            expect_mountpoint.append('%s.%s' % (
                hello_conf.appname, extra_domain))
            expect_mountpoint.append('%s.%s/web' %
                                     (hello_conf.appname, extra_domain))

        my_mountpoint.sort()
        expect_mountpoint.sort()
        assert my_mountpoint == expect_mountpoint

        my_mountpoint1 = hello_conf.procs['admin'].mountpoint
        expect_mountpoint1 = [
            '%s.%s/admin' % (hello_conf.appname, DOMAIN),
            '%s.lain/admin' % hello_conf.appname
        ]
        for extra_domain in FIXTURES_EXTRA_DOMAINS:
            expect_mountpoint1.append('%s.%s/admin' %
                                      (hello_conf.appname, extra_domain))
        my_mountpoint1.sort()
        expect_mountpoint1.sort()
        assert my_mountpoint1 == expect_mountpoint1

        # resource instance test
        resource_instance_meta_yaml = '''
                    appname: resource.demo-service.hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "hello"
                            image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                            cmd: ./proxy
                            port: 4321
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        mountpoint:
                            - /web
                            - a.foo
                            - c.com/y/z
                    web.admin:
                        cmd: admin
                        port: 80
                        mountpoint:
                            - /admin
                    notify:
                        slack: "#demo-service"
                    '''
        repo_name = 'resource.demo-service.hello'
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        r_conf = LainConf()
        r_conf.load(resource_instance_meta_yaml, repo_name, meta_version)
        assert r_conf.appname == 'resource.demo-service.hello'
        my_mountpoint = r_conf.procs['web'].mountpoint
        app_domain = 'hello.demo-service.resource'
        expect_mountpoint = ['a.foo', 'c.com/y/z',
                             '%s.%s' % (app_domain, DOMAIN),
                             '%s.lain' % app_domain,
                             '%s.%s/web' % (app_domain, DOMAIN),
                             '%s.lain/web' % app_domain
                             ]
        my_mountpoint.sort()
        expect_mountpoint.sort()
        assert my_mountpoint == expect_mountpoint

        my_mountpoint1 = r_conf.procs['admin'].mountpoint
        expect_mountpoint1 = [
            '%s.%s/admin' % (app_domain, DOMAIN),
            '%s.lain/admin' % app_domain
        ]
        my_mountpoint1.sort()
        expect_mountpoint1.sort()
        assert my_mountpoint1 == expect_mountpoint1

    def test_lain_conf_auto_append_default_mountpoint_for_procname_web(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        mountpoint:
                            - a.foo
                            - a.foo/search
                            - b.foo.bar/x
                            - c.com/y/z
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None, domains=[
                        DOMAIN] + FIXTURES_EXTRA_DOMAINS)
        assert hello_conf.appname == 'hello'
        my_mountpoint = hello_conf.procs['web'].mountpoint
        expect_mountpoint = ['a.foo', 'a.foo/search', 'b.foo.bar/x', 'c.com/y/z',
                             '%s.%s' % (hello_conf.appname, DOMAIN),
                             '%s.lain' % hello_conf.appname
                             ]
        expect_mountpoint += ['%s.%s' % (hello_conf.appname, d)
                              for d in FIXTURES_EXTRA_DOMAINS]
        my_mountpoint.sort()
        expect_mountpoint.sort()
        assert my_mountpoint == expect_mountpoint

        # resource instance test
        resource_instance_meta_yaml = '''
                    appname: resource.demo-service.hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "hello"
                            image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                            cmd: ./proxy
                            port: 4321
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        mountpoint:
                            - a.foo
                            - a.foo/search
                            - b.foo.bar/x
                            - c.com/y/z
                    notify:
                        slack: "#demo-service"
                    '''
        repo_name = 'resource.demo-service.hello'
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        r_conf = LainConf()
        r_conf.load(resource_instance_meta_yaml, repo_name, meta_version)
        assert r_conf.appname == 'resource.demo-service.hello'
        app_domain = 'hello.demo-service.resource'
        my_mountpoint = r_conf.procs['web'].mountpoint
        expect_mountpoint = ['a.foo', 'a.foo/search', 'b.foo.bar/x', 'c.com/y/z',
                             '%s.%s' % (app_domain, DOMAIN),
                             '%s.lain' % app_domain
                             ]
        my_mountpoint.sort()
        expect_mountpoint.sort()
        assert my_mountpoint == expect_mountpoint

    def test_lain_conf_no_mountpoint_for_web_type_but_name_is_not_web_proc_should_raise_exception(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web.foo:
                        cmd: foo
                        memory: 64m
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        with pytest.raises(Exception) as e:
            hello_conf.load(meta_yaml, meta_version, None)
            assert 'proc (type is web but name is not web) should have own mountpoint.' in str(
                e.value)

        # resource instance test
        resource_instance_meta_yaml = '''
                    appname: resource.demo-service.hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "hello"
                            image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                            cmd: ./proxy
                            port: 4321
                    web.foo:
                        cmd: foo
                        memory: 64m
                    notify:
                        slack: "#demo-service"
                    '''
        repo_name = 'resource.demo-service.hello'
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        r_conf = LainConf()
        with pytest.raises(Exception) as e:
            r_conf.load(meta_yaml, repo_name, meta_version)
            assert 'proc (type is web but name is not web) should have own mountpoint.' in str(
                e.value)

    def test_lain_conf_service_abbreviation(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "**"
                            cmd: ./proxy
                            port: 4321
                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['echo'].port[1234].port == 1234
        assert hello_conf.procs['echo'].type == ProcType.worker
        assert hello_conf.procs['portal-echo'].port[4321].port == 4321
        assert hello_conf.procs['portal-echo'].type == ProcType.portal

    def test_lain_conf_service_full_definition(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test

                    proc.echo:
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3

                    portal.portal-echo:
                        service_name: echo
                        allow_clients: "**"
                        cmd: ./proxy
                        port: 4321

                    notify:
                        slack: "#hello"
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, meta_version, None)
        assert hello_conf.appname == 'hello'
        assert hello_conf.procs['echo'].port[1234].port == 1234
        assert hello_conf.procs['echo'].type == ProcType.worker
        assert hello_conf.procs['portal-echo'].port[4321].port == 4321
        assert hello_conf.procs['portal-echo'].type == ProcType.portal

    def test_lain_conf_use_services_smoke(self):
        meta_yaml = '''
                    appname: echo-client
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    use_services:
                        echo-server:
                            - echo1
                            - echo2
                        bark-server:
                            - bark1
                    proc.echo-client:
                        cmd: ./ping echo1 echo2 bark1 -p 4321
                    '''
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        echoclient_conf = LainConf()
        echoclient_conf.load(meta_yaml, meta_version, None)
        assert echoclient_conf.appname == 'echo-client'
        assert echoclient_conf.use_services == {
            'echo-server': ["echo1", "echo2"],
            'bark-server': ["bark1"]
        }
        assert echoclient_conf.procs['echo-client'].type == ProcType.worker

    def test_lain_conf_resource_instance_abbreviation(self):
        meta_yaml = '''
                    appname: resource.demo-service.hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    service.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3
                        portal:
                            allow_clients: "hello"
                            image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                            cmd: ./proxy
                            port: 4321
                    notify:
                        slack: "#demo-service"
                    '''
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        r_conf = LainConf()
        r_conf.load(meta_yaml, meta_version, None)
        assert r_conf.appname == 'resource.demo-service.hello'
        assert r_conf.procs['echo'].port[1234].port == 1234
        assert r_conf.procs['echo'].type == ProcType.worker
        assert r_conf.procs[
            'echo'].image == "regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc"
        assert r_conf.procs['portal-echo'].port[4321].port == 4321
        assert r_conf.procs['portal-echo'].type == ProcType.portal
        assert r_conf.procs[
            'portal-echo'].image == "regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc"

    def test_lain_conf_resource_instance_full_definition(self):
        meta_yaml = '''
                    appname: resource/demo-service/hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test

                    proc.echo:
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./echo -p 1234
                        port: 1234
                        num_instances: 3

                    portal.portal-echo:
                        service_name: echo
                        allow_clients: "hello"
                        image: regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc
                        cmd: ./proxy
                        port: 4321

                    notify:
                        slack: "#demo-service"
                    '''
        repo_name = 'resource/demo-service/hello'
        meta_version = '1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc'
        r_conf = LainConf()
        r_conf.load(meta_yaml, meta_version, None)
        assert r_conf.appname == 'resource/demo-service/hello'
        assert r_conf.procs['echo'].port[1234].port == 1234
        assert r_conf.procs['echo'].type == ProcType.worker
        assert r_conf.procs[
            'echo'].image == "regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc"
        assert r_conf.procs['portal-echo'].port[4321].port == 4321
        assert r_conf.procs['portal-echo'].type == ProcType.portal
        assert r_conf.procs['portal-echo'].service_name == 'echo'
        assert r_conf.procs['portal-echo'].allow_clients == 'hello'
        assert r_conf.procs[
            'portal-echo'].image == "regsitry.lain.local/demo-service:release-1428553798-7142797e64bb7b4d057455ef13de6be156ae81cc"

    def test_lain_conf_use_resources_smoke(self):
        meta_yaml = '''
                    appname: echo-client
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    use_resources:
                        echo-server:
                            memory: 128M
                            cpu: 2
                            services:
                                - echo1
                                - echo2
                        bark-server:
                            services:
                                - bark1
                    proc.echo-client:
                        cmd: ./ping echo1 echo2 bark1 -p 4321
                    '''
        repo_name = 'echo-client'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        echoclient_conf = LainConf()
        echoclient_conf.load(meta_yaml, meta_version, None)
        assert echoclient_conf.appname == 'echo-client'
        assert echoclient_conf.use_resources == {
            'echo-server': {
                'services': ["echo1", "echo2"],
                'context': {
                    'cpu': 2,
                    'memory': '128M'
                }
            },
            'bark-server': {
                'services': ["bark1"],
                'context': {}
            }
        }
        assert echoclient_conf.procs['echo-client'].type == ProcType.worker

    def test_lain_conf_default_system_volumes(self):
        meta_yaml = '''
                    appname: echo-client
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    use_resources:
                        echo-server:
                            memory: 128M
                            cpu: 2
                            services:
                                - echo1
                                - echo2
                        bark-server:
                            services:
                                - bark1
                    proc.echo-client:
                        cmd: ./ping echo1 echo2 bark1 -p 4321
                    '''
        repo_name = 'echo-client'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        echoclient_conf = LainConf()
        echoclient_conf.load(meta_yaml, repo_name, meta_version)
        assert echoclient_conf.appname == 'echo-client'
        for proc in echoclient_conf.procs.values():
            assert proc.system_volumes == DEFAULT_SYSTEM_VOLUMES

    def test_lain_conf_cloud_volumes_multi_type(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                        script:
                            - echo buildscript1
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        cloud_volumes:
                            dirs:
                                - /data
                                - /var/lib/mysql
                    '''
        repo_name = 'hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        echoclient_conf = LainConf()
        echoclient_conf.load(meta_yaml, repo_name, meta_version)
        assert echoclient_conf.appname == 'hello'
        assert echoclient_conf.procs['web'].cloud_volumes.get(
            'multi') == ['/data', '/var/lib/mysql']
        print echoclient_conf.procs['web'].cloud_volumes

    def test_lain_conf_cloud_volumes_single_type(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                        script:
                            - echo buildscript1
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    test:
                        script:
                            - go test
                    web:
                        cmd: hello
                        port: 80
                        memory: 64m
                        cloud_volumes:
                            type: single
                            dirs:
                                - /data
                                - /var/lib/mysql
                    '''
        repo_name = 'hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        echoclient_conf = LainConf()
        echoclient_conf.load(meta_yaml, repo_name, meta_version)
        assert echoclient_conf.appname == 'hello'
        assert echoclient_conf.procs['web'].cloud_volumes.get('multi') == None
        assert echoclient_conf.procs['web'].cloud_volumes.get(
            'single') == ['/data', '/var/lib/mysql']
        print echoclient_conf.procs['web'].cloud_volumes

    def test_lain_conf_volume_backup(self):
        meta_yaml = '''
                    appname: echo-client
                    build:
                        base: golang
                        prepare:
                            - echo prepare1
                            - echo prepare2
                        script:
                            - echo buildscript1
                            - echo buildscript2
                    release:
                        dest_base: ubuntu
                        copy:
                            - src: hello
                              dest: /usr/bin/hello
                            - src: entry.sh
                              dest: /entry.sh
                    proc.echo-client:
                        cmd: ./ping echo1 echo2 bark1 -p 4321
                        volumes:
                          - /etc/hello:
                              backup_full:
                                schedule: "* 1 * * *"
                                expire: 30d
                                pre_run: backup.sh
                                post_run: end.sh
                              backup_increment:
                                schedule: "0 1 * * *"
                                expire: 3d
                                pre_run: backup.sh
                                post_run: end.sh
                          - /data/backupfile:
                              backup_full:
                                schedule: "* 1 * * *"
                                expire: 30d
                                pre_run: backup.sh
                                post_run: end.sh
                    '''
        repo_name = 'echo-client'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        echoclient_conf = LainConf()
        echoclient_conf.load(meta_yaml, repo_name, meta_version)

        assert len(echoclient_conf.procs['echo-client'].backup) == 3
        for backup_info in echoclient_conf.procs['echo-client'].backup:
            assert backup_info['procname'] == 'echo-client.worker.echo-client'
            if backup_info['volume'] == "/data/backupfile":
                assert backup_info['volume'] == "/data/backupfile"
                assert backup_info['schedule'] == "* 1 * * *"
                assert backup_info['expire'] == "30d"
                assert backup_info['preRun'] == "backup.sh"
                assert backup_info['postRun'] == "end.sh"
                assert backup_info['mode'] == "full"
            elif backup_info['volume'] == "/etc/hello":
                assert backup_info['volume'] == "/etc/hello"
                assert backup_info['preRun'] == "backup.sh"
                assert backup_info['postRun'] == "end.sh"
                if backup_info['mode'] == 'increment':
                    assert backup_info['schedule'] == "0 1 * * *"
                    assert backup_info['expire'] == "3d"
                    assert backup_info['mode'] == "increment"
                else:
                    assert backup_info['schedule'] == "* 1 * * *"
                    assert backup_info['expire'] == "30d"
                    assert backup_info['mode'] == "full"

    def test_lain_conf_setuptime_and_killtimeout(self):
        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                    web:
                       cmd: test
                    '''
        repo_name = 'lain/hello'
        meta_version = '1428553798.443334-7142797e64bb7b4d057455ef13de6be156ae81cc'
        hello_conf = LainConf()
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.procs['web'].setup_time == MIN_SETUP_TIME
        assert hello_conf.procs['web'].kill_timeout == MIN_KILL_TIMEOUT

        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                    web:
                       cmd: test
                       setup_time: 2342
                       kill_timeout: 1
                    '''
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.procs['web'].setup_time == MAX_SETUP_TIME
        assert hello_conf.procs['web'].kill_timeout == MIN_KILL_TIMEOUT

        meta_yaml = '''
                    appname: hello
                    build:
                        base: golang
                    web:
                       cmd: test
                       setup_time: 10
                       kill_timeout: 20
                    '''
        hello_conf.load(meta_yaml, repo_name, meta_version)
        assert hello_conf.procs['web'].setup_time == 10
        assert hello_conf.procs['web'].kill_timeout == 20


REDIS_CLIENT_META = '''
appname: hello

build:
  base: golang
  script:
    - go build -o hello

release:
  dest_base: ubuntu
  copy:
    - src: hello
      dest: /usr/bin/hello

use_resources:
  redis:
    memory: 128M
    services:
      - redis

web:
  cmd: /hello
  env:
    - REDIS_ADDR: redis:3333
'''
REDIS_CLIENT_META_VERSION = '1439365341-06e92b4456116ad5e6875c8c34797d22156d44a5'

REDIS_RESOURCE_META = '''
appname: redis
apptype: resource

build:
  base: golang
  script:
    - go build -o hello

release:
  dest_base: ubuntu
  copy:
    - src: hello
      dest: /usr/bin/hello

service.redis:
  cmd: redis -p 3333
  port: 3333
  memory: "{{ memory|default('64M') }}"
  portal:
    image: myregistry.lain.org/proxy:release-1234567-abc
    cmd: ./proxy
'''
REDIS_RESOURCE_META_VERSION = '1439365340-06e92b4456116ad5e6875c8c34797d22156d44a5'

MYSQL_CLIENT_META = '''
appname: hello

build:
  base: golang
  script:
    - go build -o hello

release:
  dest_base: ubuntu
  copy:
    - src: hello
      dest: /usr/bin/hello

use_resources:
  mysql:
    memory: 128M
    num_instances: 2
    services:
      - mysqld

web:
  cmd: /hello
  env:
    - MYSQL_ADDR: mysqld:3309
'''
MYSQL_CLIENT_META_VERSION = '1439365342-06e92b4456116ad5e6875c8c34797d22156d44a5'

MYSQL_RESOURCE_META = '''
appname: mysql
apptype: resource

build:
  base: golang
  script:
    - go build -o hello

release:
  dest_base: ubuntu
  copy:
    - src: hello
      dest: /usr/bin/hello

worker.mysqld:
  image: mysql:5.6
  cmd: mysqld {{ memory|default('64M') }}
  port: 3306
  num_instances: "{{ num_instances|default(1)|int(1) }}"
  memory: "{{ memory|default('64M') }}"

portal.mysqlproxy:
  service_name: mysqld
  image: myregistry.lain.org/proxy:release-1234567-abc
  cmd: mysqlproxy
  port: 3309
'''
MYSQL_RESOURCE_META_VERSION = '1439365343-06e92b4456116ad5e6875c8c34797d22156d44a5'


def test_resource_instance_meta_render_abbreviation():
    resource_appname = 'redis'
    resource_meta_version = REDIS_RESOURCE_META_VERSION
    resource_meta_template = REDIS_RESOURCE_META
    client_appname = 'hello'
    client_meta = REDIS_CLIENT_META
    client_meta_version = REDIS_CLIENT_META_VERSION
    registry = 'registry.lain.local'
    domain = 'lain.local'
    hello_config = LainConf()
    hello_config.load(client_meta, client_meta_version, None,
                      registry=registry, domain=domain)
    context = hello_config.use_resources[resource_appname]['context']
    resource_instance_meta = render_resource_instance_meta(
        resource_appname, resource_meta_version, resource_meta_template,
        client_appname, context, registry, domain
    )
    resource_default_image = '{}/{}:release-{}'.format(
        registry, resource_appname, resource_meta_version
    )
    resource_instance_yaml = yaml.safe_load(resource_instance_meta)
    assert not resource_instance_yaml.has_key('apptye')
    resource_instance_config = LainConf()
    resource_instance_config.load(resource_instance_meta,
                                  resource_meta_version,
                                  resource_default_image,
                                  registry=registry,
                                  domain=domain,
                                  )
    assert resource_instance_config.appname == 'resource.redis.hello'
    redis_proc = resource_instance_config.procs['redis']
    assert redis_proc.memory == '128M'
    assert redis_proc.image == resource_default_image
    portalredis_proc = resource_instance_config.procs['portal-redis']
    assert portalredis_proc.image == 'myregistry.lain.org/proxy:release-1234567-abc'


def test_resource_instance_meta_render_full():
    resource_appname = 'mysql'
    resource_meta_version = MYSQL_RESOURCE_META_VERSION
    resource_meta_template = MYSQL_RESOURCE_META
    client_appname = 'hello'
    client_meta = MYSQL_CLIENT_META
    client_meta_version = MYSQL_CLIENT_META_VERSION
    registry = 'registry.lain.local'
    domain = 'lain.local'
    hello_config = LainConf()
    hello_config.load(client_meta, client_meta_version, None,
                      registry=registry, domain=domain)
    context = hello_config.use_resources[resource_appname]['context']
    resource_instance_meta = render_resource_instance_meta(
        resource_appname, resource_meta_version, resource_meta_template,
        client_appname, context, registry, domain
    )
    resource_default_image = '{}/{}:release-{}'.format(
        registry, resource_appname, resource_meta_version
    )
    resource_instance_yaml = yaml.safe_load(resource_instance_meta)
    assert not resource_instance_yaml.has_key('apptye')
    resource_instance_config = LainConf()
    resource_instance_config.load(resource_instance_meta,
                                  resource_meta_version,
                                  None,
                                  registry=registry,
                                  domain=domain,
                                  )
    assert resource_instance_config.appname == 'resource.mysql.hello'
    mysqld_proc = resource_instance_config.procs['mysqld']
    assert mysqld_proc.memory == '128M'
    assert mysqld_proc.num_instances == 2
    assert mysqld_proc.image == 'mysql:5.6'
    assert mysqld_proc.cmd == ['mysqld', '128M']
    mysqlproxy_proc = resource_instance_config.procs['mysqlproxy']
    assert mysqlproxy_proc.image == 'myregistry.lain.org/proxy:release-1234567-abc'


def test_build_section_with_old_prepare(old_prepare_yaml):
    app_meta_version = '123456-abcdefg'
    app_conf = LainConf()
    app_conf.load(old_prepare_yaml, 'console', app_meta_version,
                  domains=['registry.lain.local', 'lain.local'])
    assert app_conf.build.base == 'sunyi00/centos-python:1.0.0'
    assert app_conf.build.script == ['( pip install -r pip-req.txt )']
    assert app_conf.build.build_arg == ['ARG1=arg1', 'ARG2=arg2']
    assert app_conf.build.prepare.version == "0"
    assert app_conf.build.prepare.keep == []
    assert app_conf.build.prepare.script == [
        '( touch /sbin/modprobe && chmod +x /sbin/modprobe )',
        '( pip install -r pip-req.txt )',
        '( rm -rf /lain/app/* )',
        '( ls -1 | xargs rm -rf )'
    ]
    assert not app_conf.procs['web'].stateful


def test_build_section_with_new_prepare(new_prepare_yaml):
    app_meta_version = '123456-abcdefg'
    app_conf = LainConf()
    app_conf.load(new_prepare_yaml, 'console', app_meta_version,
                  domains=['registry.lain.local', 'lain.local'])
    assert app_conf.build.base == 'sunyi00/centos-python:1.0.0'
    assert app_conf.build.script == ['( pip install -r pip-req.txt )']
    assert app_conf.build.build_arg == ['ARG1=arg1', 'ARG2=arg2']
    assert app_conf.build.prepare.version == "0"
    assert app_conf.build.prepare.keep == [
        'node_modules',
        'bundle'
    ]
    assert app_conf.build.prepare.script == [
        '( touch /sbin/modprobe && chmod +x /sbin/modprobe )',
        '( pip install -r pip-req.txt )',
        '( rm -rf /lain/app/* )',
        '( ls -1 | grep -v \'\\bnode_modules\\b\' | grep -v \'\\bbundle\\b\' | xargs rm -rf )'
    ]
    assert app_conf.procs['web'].stateful


def test_proc_section_with_healthcheck(healthcheck_yaml):
    app_meta_version = '123456-abcdefg'
    app_conf = LainConf()
    app_conf.load(healthcheck_yaml, 'console', app_meta_version,
                  domains=['registry.lain.local', 'lain.local'])
    assert app_conf.build.base == 'sunyi00/centos-python:1.0.0'
    assert app_conf.build.script == ['( pip install -r pip-req.txt )']
    assert app_conf.build.prepare.version == "0"
    assert app_conf.build.prepare.keep == [
        'node_modules',
        'bundle'
    ]
    assert app_conf.build.prepare.script == [
        '( touch /sbin/modprobe && chmod +x /sbin/modprobe )',
        '( pip install -r pip-req.txt )',
        '( rm -rf /lain/app/* )',
        '( ls -1 | grep -v \'\\bnode_modules\\b\' | grep -v \'\\bbundle\\b\' | xargs rm -rf )'
    ]
    annotation = json.loads(app_conf.procs['web'].annotation)
    assert annotation['healthcheck'] == '/kg/health/check'
    assert app_conf.procs['web'].healthcheck == '/kg/health/check'


def test_release(release_yaml):
    app_meta_version = '123456-abcdefg'
    app_conf = LainConf()
    app_conf.load(release_yaml, 'release', app_meta_version,
                  domains=['registry.lain.local', 'lain.local'])
    assert app_conf.release.copy == [
        {'dest': '/usr/bin/hello', 'src': 'hello'}, {'dest': 'hi', 'src': 'hi'}]
