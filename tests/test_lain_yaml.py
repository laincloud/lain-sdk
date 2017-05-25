#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lain_sdk.lain_yaml import LainYaml

YAML = 'tests/lain.yaml'


class TestLainYaml:

    def test_initialization(self):
        y = LainYaml(YAML, ignore_prepare=True)
        y = LainYaml(ignore_prepare=True)
        y.load(open(YAML).read())

    def test_vars_accessible(self):
        y = LainYaml(ignore_prepare=True)
        y.load(open(YAML).read())
        assert y.appname == 'hello'
        assert y.build.base == 'golang'
        assert y.build.script == ['( go build -o hello )']
        assert y.release.script == []
        assert y.release.dest_base == 'ubuntu'
        assert len(y.release.copy) == 1
        assert y.release.copy[0]['src'] == 'hello'
        assert y.release.copy[0]['dest'] == '/usr/bin/hello'
        assert y.test.script == ['( go test )']
        assert y.procs['web'].cmd == ['hello']
        assert y.procs['web'].setup_time == 40
        assert y.procs['web'].kill_timeout == 30

    def test_prepare_act(self):
        y = LainYaml(ignore_prepare=True)
        assert y.act == False
        y.init_act(YAML, ignore_prepare=True)
        assert y.act == True
        assert len(y.img_names) == 5
        assert len(y.img_temps) == 5
        assert len(y.img_builders) == 5

        y = LainYaml(YAML, ignore_prepare=True)
        assert y.act == True
        assert len(y.img_names) == 5
        assert len(y.img_temps) == 5
        assert len(y.img_builders) == 5
