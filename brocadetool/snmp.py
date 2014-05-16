from pysnmp.entity.rfc3413.oneliner import cmdgen

#from pysnmp import debug
#debug.setLogger(debug.Debug('all'))


def get(self, snmp_type, snmp_args):
    cmd_gen = cmdgen.CommandGenerator()

    error_indication, error_status, error_index, var_binds = getattr(cmd_gen,
                                                                     snmp_type)(
        cmdgen.CommunityData(self.passwd),
        cmdgen.UdpTransportTarget((self.host, 161)),
        getattr(cmdgen, 'MibVariable')(*snmp_args),
        lookupNames=True, lookupValues=True
    )

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
