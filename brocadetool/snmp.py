from pysnmp.entity.rfc3413.oneliner import cmdgen

def get(self):
        snmp_output = {}
        cmd_gen = cmdgen.CommandGenerator()

        error_indication, error_status, error_index, var_binds = cmd_gen\
            .getCmd(
            cmdgen.CommunityData(self.passwd),
            cmdgen.UdpTransportTarget((self.host, 161)),
            cmdgen.MibVariable('IF-MIB', self.stat,
                               '0'),
            lookupNames=True, lookupValues=True
        )

        # Check for errors and print out results
        if error_indication:
            raise RuntimeError(error_indication)
        else:
            if error_status:
                msg = ('%s at %s' % (
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index)-1] or '?'
                    )
                )
                raise RuntimeError(msg)
            else:
                for name, val in var_binds:
                    print('%s = %s' % (name.prettyPrint(), val.prettyPrint(
                     )))
                    snmp_output[name.prettyPrint()] = val.prettyPrint()
                    #if self.debug:
                    #    print('%s = %s' % (name, val))

                return snmp_output
