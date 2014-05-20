from pysnmp.entity.rfc3413.oneliner import cmdgen

#from pysnmp import debug
#debug.setLogger(debug.Debug('all'))


def get(self, snmp_type, snmp_args):
    cmd_gen = cmdgen.CommandGenerator()

    error_indication, error_status, error_index, var_binds = getattr(cmd_gen,
                                                                     snmp_type)(
        cmdgen.CommunityData(self.passwd),
        cmdgen.UdpTransportTarget((self.host, 161)),
        getattr(cmdgen, 'MibVariable')(*snmp_args), lookupNames=True,
        lookupValues=True)

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
    snmp_type = 'getCmd'
    snmp_args = ('IF-MIB', stat, self.start_port_index)

    output = get(self, snmp_type, snmp_args)
    return output[0][0].getMibNode().getName()


def get_index_value(self, oid_node):
    key_value = {}
    snmp_type = 'nextCmd'
    snmp_args = (oid_node,)

    output = get(self, snmp_type, snmp_args)
    for entry in output:
        key = entry[0][0].getOid().prettyPrint().split('.')[-1]
        value = entry[0][1].prettyPrint()
        key_value[key] = {'name': value }

    return key_value
