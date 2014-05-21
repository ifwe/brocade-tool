#!/usr/bin/env python

import argparse
import json
import logging
import os
import socket
import subprocess
import sys

import snmp
import utils

from pysnmp import debug


class IsPingableAction(argparse.Action):
    """
    Used by argparse to see if the NetScaler specified is alive (pingable)
    """

    def __call__(self, parser, namespace, values, option_string=None):
        pingCmd = "ping -c 1 -W 2 %s" % (values)
        process = subprocess.call(
            pingCmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if process != 0:
            msg = "%s is not alive." % (values)
            print >> sys.stderr, msg
            return sys.exit(1)

        setattr(namespace, self.dest, values)


class Base(object):
    def __init__(self, args):
        self.debug = args.debug
        self.host = args.host

        try:
            self.config = utils.fetch_config(args.config_file)
        except IOError:
            raise

        self.passwd = self.config['passwd']
        self.start_port_index = self.config['start_port_index']

    def get_port_ids(self, oid_node):
        ports = {}
        snmp_type = 'nextCmd'
        snmp_args = (oid_node,)

        output = snmp.get(self.host, self.passwd, snmp_type, snmp_args)
        for entry in output:
            ports[(entry[0][0].getOid().prettyPrint()).split('.')[-1]]


class Show(Base):
    def __init__(self, args):
        super(Show, self).__init__(args)
        self.stat = args.stat

    def ports(self):
        """
        Show all ports or specific stats, if --stat is given as an argument
        """
        oid_node = snmp.get_oid_node(self, 'ifName')
        ifname_key_value = snmp.get_index_value(self, 'ifName', oid_node)

        if not self.stat:
            for key, value in sorted(ifname_key_value.iteritems()):
                print(value['ifName'])
        else:
            for stat in self.stat:
                oid_node = snmp.get_oid_node(self, stat)
                stat_key_value = snmp.get_index_value(self, stat, oid_node)
                for key, value in stat_key_value.iteritems():
                    old_value = (ifname_key_value[key])
                    value.update(old_value)
                    ifname_key_value[key] = value

            print(json.dumps(ifname_key_value))


def main():
    """
    Main function
    @return: Exit status
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
    except (socket.herror, socket.gaierror), e:
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
    parser.add_argument(
        "host", metavar='BROCADE', action=IsPingableAction, help="IP or \
        name of Brocade"
    )
    parser.add_argument(
        "--passwd", dest="passwd", help="Community password for brocade user. \
        Default is to fetch from brocadetool.conf"
    )
    parser.add_argument(
        "--debug", action="store_true", dest="debug", help="Shows what's \
        going on", default=False
    )

    # Creating subparser.
    subparser = parser.add_subparsers(dest="topSubparserName")

    # Creating show subparser.
    parser_show = subparser.add_parser(
        "show", help="sub-command for showing objects"
    )
    subparser_show = parser_show.add_subparsers(dest="subparserName")
    parser_show_ports = subparser_show.add_parser("ports",
                                                  help="sub-command for "
                                                       "showing stats about "
                                                       "all ports")
    parser_show_ports.add_argument("--stat", nargs="+",
                                   help="What stat(s) to show")

    # Getting arguments
    args = parser.parse_args()

    if args.debug:
        debug.setLogger(debug.Debug('all'))

    # Getting method, based on subparser called from argparse.
    method = args.subparserName.replace('-', '')

    # Getting class, based on subparser called from argparse.
    try:
        klass = globals()[args.topSubparserName.capitalize()]
    except KeyError:
        msg = "%s, %s is not a valid subparser." % (user,
                                                    args.topSubparserName)
        print >> sys.stderr, msg
        logger.critical(msg)
        return 1

    try:
        brocade_tool = klass(args)
    except:
        print >> sys.stderr, sys.exc_info()[1]
        logger.critical(sys.exc_info()[1])
        return 1

    try:
        getattr(brocade_tool, method)()
        msg = "%s executed \'%s\' on %s" % (user, args, args.host)
        logger.info(msg)
    except (AttributeError, RuntimeError, KeyError, IOError) as e:
        msg = "%s, %s" % (user, e)
        print >> sys.stderr, msg
        logger.critical(msg)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
