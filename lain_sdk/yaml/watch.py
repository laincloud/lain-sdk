#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib
import pickle
from fnmatch import fnmatch

from util import load_yaml
from ..util import rm


class PathWatcher(object):
    """Watch directory or file for change

    If `path` is a directory, walk through it, 
    return whether any file under this directory has been changed.

    If `path` is a file, return whether it's changed.

    set a list of absolute paths as `ignore_paths` to ignore some paths' change

    Current implementation leveraging md5
    """

    def __init__(self, path, ignore_paths=[]):
        self._dump = '/tmp/.lain_watcher_{}'.format(
            hashlib.sha1(path).hexdigest())

        self.path = path
        if self.path.endswith('/') and len(self.path) > 1:
            self.path = self.path[:-1]

        # path in patterns relative to self.path, not starting with "./"
        self.ignore_patterns = []
        for path in ignore_paths:
            if path.endswith('/') and len(path) > 1:
                path = path[:-1]
            # translate directories like d to d/*
            if os.path.isdir(path):
                self.ignore_patterns.append(path)
                path = path + "/*"
            self.ignore_patterns.append(path)

        if os.path.exists(self._dump):
            with open(self._dump) as f:
                self.snapshot = pickle.loads(f.read())
        else:
            self.snapshot = {}

    def _hash(self, path):
        h = hashlib.md5()
        try:
            with open(path) as f:
                h.update(f.read())
            return h.hexdigest()
        except Exception:
            return None

    def is_ignored(self, path):
        for pattern in self.ignore_patterns:
            if fnmatch(path, pattern):
                return True
        return False

    def update(self):
        new_snapshot = {}
        if os.path.isfile(self.path):
            new_snapshot = {self.path: self._hash(self.path)}
        elif os.path.isdir(self.path):
            for dirpath, dirnames, filenames in os.walk(self.path):
                # self.path './yy' dirpath './yy/xxxx' => 'xxxx'
                # self.path '/x/y' dirpath '/x/y/z' => 'z'
                dirpath = dirpath[len(self.path) + 1:]
                if self.is_ignored(dirpath):
                    continue
                for filename in filenames:
                    filename = os.path.join(dirpath, filename)
                    if self.is_ignored(filename):
                        continue
                    new_snapshot[filename] = self._hash(filename)
        changed = new_snapshot != self.snapshot
        old = self.snapshot
        self.snapshot = new_snapshot
        with open(self._dump, 'w') as f:
            f.write(pickle.dumps(self.snapshot))
        return old

    def is_changed(self):
        return self.update() != self.snapshot

    def refresh(self):
        rm(self._dump)
