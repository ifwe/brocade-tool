#!/usr/bin/env python

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

import argparse
import json
import logging
import os
import socket
import subprocess
import sys
from collections import OrderedDict
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
    def __init__(self, args, logger):
        try:
            self.config = utils.fetch_config(args['config_file'])
        except IOError:
            raise

        for k, v in args.items():
            if k not in self.config:
                self.config[k] = v

        if args['carbon']:
            self.carbon_server = self.config['carbon_server']
            self.carbon_port = self.config['carbon_port']
            self.carbon_metric_base = self.config['carbon_metric_base']

        self.logger = logger


class Show(Base):
    def ports(self):
        """
        Show all stat information or specific stats, if --stat is given as an
        argument
        """
        all_port_info = dict()
        previous_port_rate_data = dict()

        try:
            previous_data_file = '%s/%s_previous_data.json' % (
                self.config['previous_data_path'], self.config['host']
            )
        except KeyError as exc:
            msg = "Missing %s from %s" % (exc, self.config['config_file'])
            raise brocade_exceptions.BadConfig(msg)

        # Detecting if we will use stats from config or cli
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

        # Read in any previous data from last run
        try:
            with open(previous_data_file, 'r') as fh:
                previous_port_rate_data = json.load(fh)
        except (IOError, ValueError) as exc:
            msg = "No previous data found in %s. This is probably OK, if we " \
                  "haven't cared about any previous data before or no oid " \
                  "entries need to keep track of rates: %s" % \
                  (previous_data_file, exc)
            self.logger.warning(msg)
            pass

        # Lopping through all stats
        for stat in self.config['stat']:
            # If invalid stat we specified, probably from cli
            try:
                oid = self.config['oids'][stat]
            except KeyError as exc:
                msg = "%s could not be found in %s" % (
                    stat, self.config['config_file']
                )
                raise brocade_exceptions.BadConfig(msg)

            # For the case when we have to detect if an stat/oid needs to be
            # monitored for rate changes
            if isinstance(oid, list) and oid[1] == 'rate':
                oid = oid[0]
                enable_rate = True
            else:
                enable_rate = False

            for port, value in sorted(snmp.get_info(self.config, oid).items(

            ), key=lambda (port, value): int(port)):
                if enable_rate:
                    try:
                        # Taking the difference and then converting words to
                        # bits by multiplying by 4 and then 8. 1 word = 4
                        # bytes, 1 byte = 8 bits
                        rate = value - previous_port_rate_data[stat][port]
                    except (KeyError, TypeError):
                        # No previous data yet. Setting to zero, this time
                        # around
                        rate = 0
                    else:
                        # No increase in rate, so we need to force to 0 or
                        # rate will show up as being a negative number
                        if rate < 0:
                            rate = 0

                    # Updating previous data dict with latest info for next
                    # time
                    if stat in previous_port_rate_data:
                        previous_port_rate_data[stat][port] = value
                    else:
                        previous_port_rate_data[stat] = OrderedDict(
                            {port: value}
                        )
                    value = rate

                # Should we send to carbon
                if self.config['carbon']:
                    metric = "%s.%s.ports.%s.%s" % (
                        self.carbon_metric_base, self.config['host'],
                        port, stat
                    )
                    if self.config['debug']:
                        print "CARBON DATA - %s: %s" % (metric, value)

                    if not self.config['dryrun']:
                        try:
                            utils.carbon_submit(self.carbon_server,
                                                self.carbon_port,
                                                metric, value)
                        except:
                            raise

                if stat in all_port_info:
                    all_port_info[stat][port] = value
                else:
                    all_port_info[stat] = OrderedDict({port: value})

        if previous_port_rate_data:
            try:
                with open(previous_data_file, 'w') as fh:
                    json.dump(previous_port_rate_data, fh)
            except IOError as exc:
                msg = "Could not write recent data to %s: %s" % (
                    previous_data_file, exc
                )
                raise brocade_exceptions.Brocade(msg)

        if all_port_info:
            print json.dumps(all_port_info)


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
    parser.add_argument('--carbon', action='store_true', help='Send data to '
                        'carbon?', default=False)

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

    if args['carbon'] and not args['dryrun'] and args['debug']:
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
        getattr(klass(args, logger), method)()
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
