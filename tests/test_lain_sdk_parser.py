#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lain_sdk.yaml.parser import parse_path


class TestLainParser:

    def test_parse_path(self):
        somepaths = ['hello', '/ab/dfafd/ttt/fad', 'ok/../hello', '../hh',
                     '/dfadf', '/', '', ' ', 'waht/', "  hello", '   /hello',
                     '../../../hello', '../../hello']
        somenewpaths = parse_path(somepaths)
        assert somenewpaths == ['/lain/app/hello', '/ab/dfafd/ttt/fad',
                                '/lain/app/hello', '/lain/hh', '/dfadf', '/',
                                '/lain/app/', '/lain/app/ ', '/lain/app/waht/',
                                '/lain/app/  hello', '/lain/app/   /hello',
                                '/hello', '/hello']
