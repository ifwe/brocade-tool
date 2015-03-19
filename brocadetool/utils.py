"""
Copyright 2015 Ifwe Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import socket
import time
import yaml
import yaml.parser

import brocade_exceptions


def fetch_config(config_file):
    """
    Fetch configuration from file

    :param config_file: Full path to configuration file that needs to be read
    :returns: Contents of config file in YAML format
    """
    try:
        with open(config_file, 'r') as f:
            config = yaml.load(f)
    except IOError as exc:
        msg = "Could not read %s: %s" % (config_file, exc)
        raise brocade_exceptions.ErrorReadingConfig(msg)
    except yaml.parser.ParserError:
        msg = "Invalid configuration YAML format"
        raise brocade_exceptions.BadConfig(msg)

    return config


def carbon_submit(server, port, metric, value):
    """
    Send data to graphite

    :param server: Graphite server
    :param port: Graphite port
    :param metric: Metric to send
    :param value: Metric value to send
    """
    now = time.time()
    msg = "%s %s %d\n" % (metric, value, now)

    sock = socket.socket()
    try:
        sock.connect((server, port))
        sock.sendall(msg)
    except:
        raise
    finally:
        sock.close()
