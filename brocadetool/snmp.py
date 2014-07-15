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

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.smi.error import SmiError


def get(self, snmp_type, snmp_args):
    """
    snmp get, similar to snmpget or snmpwalk, depending on snmp_type

    Args:
        self: An object that makes it easier to grab the passwd and host
        snmp_type: nextCmd or getCmd.
        snmp_args: ('IF-MIB', stat, self.start_port_index) or node OID.

    Returns:
        Managed Object Instance is represented by a pair of Name and Value
        items collectively.

    Raises:
        RunTimeError.

    """
    cmd_gen = cmdgen.CommandGenerator()

    try:
        error_indication, error_status, error_index, var_binds = getattr(
            cmd_gen, snmp_type)(
                cmdgen.CommunityData(self.passwd),
                cmdgen.UdpTransportTarget((self.host, 161)),
                getattr(cmdgen, 'MibVariable')(*snmp_args), lookupNames=True)
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


def get_oid_node(self, stat):
    """
    Gets OID node based on specific stat.

    Args:
        self: An object that makes it easier to grab the password and host
        stat: SNMP MIB object

    Raises:
        RuntimeError

    Returns:
        OID node for specific stat.
    """
    snmp_type = 'getCmd'
    snmp_args = ('IF-MIB', stat, self.start_port_index)

    try:
        output = get(self, snmp_type, snmp_args)
    except (SmiError, RuntimeError) as e:
        raise RuntimeError(e)

    return output[0][0].getMibNode().getName()


def get_index_value(self, stat, oid_node):
    """
    Get values for a specific OID node, just like snmpwalk does

    Args:
        self: An object that makes it easier to grab the passwd and host.
        stat: SNMP MIB object.
        oid_node: OID Node return from get_index_value()

    Raises:
        RuntimeError

    Returns:
        A dict mapping index to values, in which values will be a dict as well.
    """
    key_value = {}
    snmp_type = 'nextCmd'
    snmp_args = (oid_node,)

    try:
        output = get(self, snmp_type, snmp_args)
    except (SmiError, RuntimeError) as e:
        raise RuntimeError(e)

    for entry in output:
        key = int(entry[0][0].getOid().prettyPrint().split('.')[-1])
        value = entry[0][1].prettyPrint()
        key_value[key] = {stat: value}

    return key_value
