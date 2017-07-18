# -*- coding: utf-8 -*-

from lain_sdk.yaml.parser import MIN_SETUP_TIME, MAX_SETUP_TIME, MIN_KILL_TIMEOUT, MAX_KILL_TIMEOUT

core_pattern = "([a-zA-Z])([a-zA-Z0-9]*)(-[a-zA-Z0-9]+)*"

appname_pattern = "^" + core_pattern + "$"
procname_pattern = "^" + core_pattern + "$"
resource_param_pattern = "(?!^services$)(^" + core_pattern + "$)"
base_proc_pattern = "^(proc\.)" + core_pattern + "$"
typed_proc_pattern = "^(web|worker|oneshot)" + "(\." + core_pattern + ")?$"
service_proc_pattern = "^(service\.)" + core_pattern + "$"
portal_proc_pattern = "^(portal\.)" + core_pattern + "$"
apptype_pattern = "^(resource|app)$"
memory_pattern = "^[1-9]+[0-9]*[mMgG]$"

path_pattern = "^.*$"

appname = {
    "description": "cluster unique name for app",
    "type": "string",
    "pattern": appname_pattern
}

giturl = {
    "description": "bind git url for app",
    "type": "string"
}

apptype = {
    "description": "apptype for app, only resource and app allowed",
    "type": "string",
    "pattern": apptype_pattern
}

backup_policy = {
    "type": "object",
    "properties": {
        "expire": {"type": "string"},
        "post_run": {"type": "string"},
        "pre_run": {"type": "string"},
        "schedule": {"type": "string"},
    },
    "additionalProperties": False,
}

cthealthcheck_options = {
    "type": "object",
    "properties": {
        "interval": {"type": "integer"},
        "timeout": {"type": "integer"},
        "retries": {"type": "integer"},
    },
    "additionalProperties": False,
}

cthealthcheck = {
    "type": "object",
    "properties": {
        "cmd": {"type": "string"},
        "options": cthealthcheck_options,
    },
    "additionalProperties": False,
    "required": ["cmd"]
}

persistent_dirs_item = {
    "oneOf": [
        {"type": "string"},
        {
            "type": "object",
            "patternProperties": {
                path_pattern: {
                    "type": "object",
                    "properties": {
                        "backup_full": backup_policy,
                        "backup_increment": backup_policy,
                    },
                },
            },
        },
    ]
}

cloud_volumes_policy = {
    "description": "mount volumes from nfs like file system",
    "type": "object",
    "properties": {
        "type": {
            "description": "whether store in one volume for all the instances",
            "items": {"type": "string"}
        },
        "dirs": {
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
    "required": ["dirs"]
}

exec_form_or_shell_form = {
    "description": "exec form or shell form similar to the one in Dockerfile",
    "oneOf": [
        {"type": "null"},
        {"type": "string"},
        {
            "type": "array",
            "items": {"type": "string"}
        }
    ]
}

memory = {
    "description": "memory limit",
    "type": "string",
    "pattern": memory_pattern
}

typed_proc_properties = {
    "user": {"type": "string"},
    "image": {"type": "string"},
    "entrypoint": exec_form_or_shell_form,
    "cmd": exec_form_or_shell_form,
    "workdir": {"type": "string"},
    "working_dir": {"type": "string"},
    "num_instances": {"type": "integer"},
    "cpu": {"type": "integer"},
    "labels": {"itmes": {"type": "string"}},
    "filters": {"itmes": {"type": "string"}},
    "memory": memory,
    "port": {"type": "integer"},
    "ports": {"itmes": {"type": "string"}},
    "healthcheck": {"type": "string"},
    "container_healthcheck": cthealthcheck,
    "env": {"items": {"type": "string"}},
    "persistent_dirs": {"items": persistent_dirs_item},
    "volumes": {"items": persistent_dirs_item},
    "cloud_volumes": cloud_volumes_policy,
    "secret_files": {"items": {"type": "string"}},
    "logs": {"items": {"type": "string"}},
    "mountpoint": {"items": {"type": "string"}},
    "https_only": {"type": "boolean"},
    "stateful": {"type": "boolean"},
    "secret_files_bypass": {"type": "boolean"},
    "kill_timeout": {"type": "integer", "minimum": MIN_KILL_TIMEOUT, "maximum": MAX_KILL_TIMEOUT},
    "setup_time": {"type": "integer", "minimum": MIN_SETUP_TIME, "maximum": MAX_SETUP_TIME},
}

base_proc_properties_extra = {
    "type": {"type": "string"},
}

base_proc_properties = dict(
    list(typed_proc_properties.items()) + list(base_proc_properties_extra.items()))

portal_proc_properties_extra = {
    "service_name": {"type": "string"},
    "allow_clients": {"type": "string"},
}

portal_proc_properties = dict(
    list(typed_proc_properties.items()) + list(portal_proc_properties_extra.items()))

service_proc_properties_extra = {
    "portal": {
        "type": "object",
        "properties": portal_proc_properties,
        "additionalProperties": False,
    },
}

service_proc_properties = dict(
    list(base_proc_properties.items()) + list(service_proc_properties_extra.items()))

build__prepare = {
    "type": "object",
    "properties": {
        "version": {
            "oneOf": [
                {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9]+$"
                },
                {
                    "type": "integer"
                },
            ]
        },
        "script": {
            "items": {"type": "string"}
        },
        "keep": {
            "items": {"type": "string"}
        },
    },
    "additionalProperties": False,
    "required": ["script"]
}

build__prepare_old = {
    "items": {"type": "string"}
}

build = {
    "description": "how to build the app",
    "type": "object",
    "properties": {
        "base": {
            "description": "base image to build the app",
            "type": "string",
        },
        "prepare": {
            "anyOf": [
                build__prepare_old,
                build__prepare
            ]
        },
        "script": {
            "description": "scripts to build the app",
            "items": {"type": "string"}
        },
        "build_arg": {
            "description": "build args to build the app",
            "items": {"type": "string"}
        },
    },
    "additionalProperties": False,
    "required": ["base", "script"]
}

test = {
    "description": "how to test the app",
    "type": "object",
    "properties": {
        "script": {
            "description": "scripts to test the app",
            "items": {"type": "string"}
        },
    },
    "additionalProperties": False,
    "required": ["script"]
}

release = {
    "description": "how to release the app",
    "type": "object",
    "properties": {
        "script": {
            "description": "scripts to run before file copy",
            "items": {"type": "string"}
        },
        "dest_base": {
            "type": "string"
        },
        "copy": {
            "items": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "integer"},
                    {
                        "type": "object",
                        "properties": {
                            "src": {"type": "string"},
                            "dest": {"type": "string"}
                        },
                    },
                ]
            },
        },
    },
    "additionalProperties": False,
    "required": ["dest_base", "copy"]
}

use_services = {
    "type": "object",
    "patternProperties": {
        appname_pattern: {
            "items": {
                "type": "string",
                "pattern": procname_pattern,
            }
        }
    },
    "additionalProperties": False,
}

use_resources = {
    "type": "object",
    "patternProperties": {
        appname_pattern: {
            "type": "object",
            "properties": {
                "services": {
                    "items": {
                        "type": "string",
                        "pattern": procname_pattern,
                    },
                },
            },
            "patternProperties": {
                resource_param_pattern: {
                    "oneOf": [
                        {
                            "type": "string",
                        },
                        {
                            "type": "integer"
                        },
                    ]
                },
            },
        },
    },
    "additionalProperties": False,
}

notify = {
    "description": "notification",
    "type": "object",
    "properties": {
        "slack": {
            "description": "channel of slack",
            "type": "string",
        },
        "bearychat": {
            "description": "channel of bearychat",
            "type": "string",
        },
    },
}

schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "lain.yaml",
    "description": "lain cluster config file for app",
    "type": "object",
    "properties": {
        "appname": appname,
        "giturl": giturl,
        "apptype": apptype,
        "build": build,
        "test": test,
        "release": release,
        "use_services": use_services,
        "use_resources": use_resources,
        "notify": notify,
    },
    "patternProperties": {
        base_proc_pattern: {
            "type": "object",
            "properties": base_proc_properties,
            "additionalProperties": False,
        },
        typed_proc_pattern: {
            "type": "object",
            "properties": typed_proc_properties,
            "additionalProperties": False,
            "anyOf": [
                {
                    "required": ["entrypoint"]
                },
                {
                    "required": ["cmd"]
                }
            ]
        },
        portal_proc_pattern: {
            "type": "object",
            "properties": portal_proc_properties,
            "additionalProperties": False,
        },
        service_proc_pattern: {
            "type": "object",
            "properties": service_proc_properties,
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
    "required": ["appname", "build"]
}
