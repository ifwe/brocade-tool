#!/usr/bin/env python

"""
Copyright 2014 Tagged Inc.

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

import argparse
import logging
import os
import socket
import subprocess
import sys
from pysnmp import debug

import snmp
import utils
import brocade_exceptions


class IsPingableAction(argparse.Action):
    """
    Used by argparse to see if the specified brocade is alive (pingable)
    """

    def __call__(self, parser, namespace, values, option_string=None):
        ping_cmd = "ping -c 1 -W 2 %s" % values
        process = subprocess.call(
            ping_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if process != 0:
            msg = "%s is not alive." % values
            print >> sys.stderr, msg
            return sys.exit(1)

        setattr(namespace, self.dest, values)


class Base(object):
    def __init__(self, args):
        try:
            self.config = utils.fetch_config(args['config_file'])
        except IOError:
            raise

        for k, v in args.items():
            if k not in self.config:
                self.config[k] = v

        if args['graphite']:
            self.graphite_server = self.config['graphite_server']
            self.graphite_port = self.config['graphite_port']
            self.graphite_metric_base = self.config['graphite_metric_base']


class Show(Base):
    def ports(self):
        """
        Show all stat information or specific stats, if --stat is given as an
        argument

        :returns: Newline separated list of ports or newline separated dict of
        ports and user specified stats.
        """

        if not self.config['stat']:
            stats = []
            try:
                for stat in self.config['oids'].keys():
                    stats.append(stat)
            except KeyError:
                msg = "Missing oids entry from config"
                raise brocade_exceptions.BadConfig(msg)
            else:
                self.config['stat'] = stats

        for stat in self.config['stat']:
            for port, value in sorted(snmp.get_index_value(self.config,
                                                           stat).items()):
                if self.config['graphite']:
                    metric = "%s.%s.ports.%s.%s" % (
                        self.graphite_metric_base, self.config['host'],
                        port, stat
                    )
                    if self.config['debug']:
                        print "GRAPHITE DATA - %s: %s" % (metric, value)

                    if not self.config['dryrun']:
                        try:
                            utils.send_to_graphite(self.graphite_server,
                                                   self.graphite_port,
                                                   metric, value)
                        except:
                            raise
                else:
                    print "stat: %s - port: %s - value: %s" % (
                        stat,  port, value
                    )


def main():
    """
    Main function

    :returns: Exit status
    """
    # Grabbing the user that is running this script for logging purposes
    if os.getenv('SUDO_USER'):
        user = os.getenv('SUDO_USER')
    else:
        user = os.getenv('USER')

    # Setting up logging
    log_file = '/var/log/brocade-tool/brocade-tool.log'
    config_file = '/etc/brocadetool.conf'

    try:
        local_host = socket.gethostbyaddr(socket.gethostname())[1][0]
    except (socket.herror, socket.gaierror):
        local_host = 'localhost'
    logger = logging.getLogger(local_host)
    logger.setLevel(logging.DEBUG)

    try:
        ch = logging.FileHandler(log_file)
    except IOError, e:
        print >> sys.stderr, e
        sys.exit(1)

    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s - %(levelname)s - %(message)s',
        datefmt='%b %d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Created parser.
    parser = argparse.ArgumentParser()

    # Set some defaults
    parser.set_defaults(config_file=config_file)

    # Global args
    parser.add_argument('host', metavar='BROCADE', action=IsPingableAction,
                        help='IP or name of Brocade')
    parser.add_argument('--passwd', help='Community password for brocade user. '
                        'Default is to fetch from brocadetool.conf')
    parser.add_argument('--dryrun', action='store_true', help='Dryrun',
                        default=False)
    parser.add_argument('--debug', action='store_true', help='Shows what\'s '
                        'going on', default=False)
    parser.add_argument('--verbose', '-v', action='count',
                        help='Shows more info')
    parser.add_argument('--graphite', action='store_true', help='Send data to '
                        'graphite?', default=False)

    # Creating subparser.
    subparser = parser.add_subparsers(dest='top_subparser_name')

    # Creating show subparser.
    parser_show = subparser.add_parser('show', help='sub-command for showing '
                                       'objects')
    subparser_show = parser_show.add_subparsers(dest='subparser_name')
    parser_show_ports = subparser_show.add_parser('ports', help='sub-command '
                                                  'for showing stats about all '
                                                  'ports')
    parser_show_ports.add_argument("--stat", nargs="+",
                                   help='What stat(s) to show per port')

    # Getting arguments
    args = vars(parser.parse_args())

    if args['dryrun']:
        print "*" * 20, "DRYRUN DRYRUN!!", "*" * 20

    if args['graphite'] and not args['dryrun'] and args['debug']:
        print "*" * 20, "WILL SEND DATA TO GRAPHITE", "*" * 20

    # Enable debug if verbose is set
    if args['verbose']:
        debug.setLogger(debug.Debug('all'))

    # Getting method, based on subparser called from argparse.
    method = args['subparser_name'].replace('-', '')

    # Getting class, based on subparser called from argparse.
    try:
        klass = globals()[args['top_subparser_name'].capitalize()]
    except brocade_exceptions.Brocade:
        msg = "%s, %s is not a valid subparser." % (user,
                                                    args['top_subparser_name'])
        print >> sys.stderr, msg
        logger.critical(msg)
        return 1

    try:
        getattr(klass(args), method)()
        msg = "%s executed \'%s\' on %s" % (user, args, args['host'])
        logger.info(msg)
    except brocade_exceptions.Brocade as exc:
        msg = "%s, %s" % (user, exc)
        print >> sys.stderr, msg
        logger.critical(msg)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
