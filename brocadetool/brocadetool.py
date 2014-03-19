#!/usr/bin/env python

import os
import sys
import pysnmp
import socket
import logging
import argparse
import subprocess


# Grabbing the user that is running this script for logging purposes
if os.getenv('SUDO_USER'):
    user = os.getenv('SUDO_USER')
else:
    user = os.getenv('USER')

# Setting up logging
logFile = '/var/log/brocade-tool/brocade-tool.log'
try:
    local_host = socket.gethostbyaddr(socket.gethostname())[1][0]
except (socket.herror, socket.gaierror), e:
    local_host = 'localhost'
logger = logging.getLogger(local_host)
logger.setLevel(logging.DEBUG)

try:
    ch = logging.FileHandler(logFile)
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


class is_pingable_action(argparse.Action):
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


class Client():
    def connect(self):
        pass

    def close(self):
        pass

    def get_value(self):
        pass


def main():
    # Created parser.
    parser = argparse.ArgumentParser()

    # Global args
    parser.add_argument(
        "host", metavar='BROCADE', action=is_pingable_action, help="IP or \
        name of Brocade"
    )
    parser.add_argument("--user", dest="user", help="Brocade user")
    parser.add_argument(
        "--passwd", dest="passwd", help="Password for brocade user. Default \
        is to fetch from brocadetool.conf for user api_user"
    )
    parser.add_argument(
        "--debug", action="store_true", dest="debug", help="Shows what's \
        going on", default=False
    )
    parser.add_argument(
        "--dryrun", action="store_true", dest="dryrun", help="Dryrun",
        default=False
    )

    # Creating subparser.
    subparser = parser.add_subparsers(dest='topSubparserName')

    # Creating show subparser.
    parser_show = subparser.add_parser(
        'show', help='sub-command for showing objects'
    )
    subparser_show = parser_show.add_subparsers(dest='subparserName')
    subparser_show.add_parser('ports', help='Shows all ports')
    parser_show_port = subparser_show.add_parser(
        'port', help='Shows stats for a port'
    )
    parser_show_port.add_argument(
        'port', help='Shows stats for a port'
    )

    # Getting arguments
    args = parser.parse_args()
    debug = args.debug

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
    except (AttributeError, RuntimeError, KeyError, IOError):
        msg = "%s, %s" % (user, sys.exc_info()[1])
        print >> sys.stderr, msg
        logger.critical(msg)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())