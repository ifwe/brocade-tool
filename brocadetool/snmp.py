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

import brocade_exceptions

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.smi.error import SmiError


def get(config, oid, snmp_type):
    """
    SNMP get, similar to snmpget or snmpwalk, depending on snmp_type

    :param self: An object that makes it easier to grab the passwd and host
    :param snmp_type: nextCmd or getCmd.
    :param snmp_args: ('IF-MIB', stat, self.start_port_index) or node OID.
    :returns: Managed Object Instance is represented by a pair of Name and Value
    items collectively.
    :raises: RunTimeError

    """
    passwd = config['passwd']
    host = config['host']
    cmd_gen = cmdgen.CommandGenerator()

    try:
        error_indication, error_status, error_index, var_binds = \
            getattr(cmd_gen, snmp_type)(
                cmdgen.CommunityData(passwd),
                cmdgen.UdpTransportTarget((host, 161)), oid
            )
    except:
        raise

    # Check for errors and print out results
    if error_indication:
        raise RuntimeError(error_indication)
    else:
        if error_status:
            msg = ('%s at %s' % (
                error_status.prettyPrint(),
                error_index and var_binds[int(error_index) - 1] or '?'
            )
            )
            raise RuntimeError(msg)
        else:
            return var_binds


def get_info(config, oid):
    """
    Get values for a specific OID node, just like snmpwalk does

    :param self: An object that makes it easier to grab the passwd and host.
    :param stat: SNMP MIB object.
    :param oid_node: OID Node return from get_info()
    :raises: RuntimeError
    :returns: A dict mapping index to values, in which values will be a dict
    as well.
    """
    port_info = {}
    snmp_type = 'nextCmd'

    try:
        output = get(config, oid, snmp_type)
    except (SmiError, RuntimeError) as exc:
        raise brocade_exceptions.Brocade(exc)

    for entry in output:
        port = entry[0][0].prettyPrint().split('.')[-1]
        value = int(entry[0][1].prettyPrint())

        port_info[port] = value

    return port_info
