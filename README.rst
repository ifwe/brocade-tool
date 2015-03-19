brocade-tool
============

System Requirements
-------------------

-  Python >= 2.6 and Python < 3
-  Python modules are in requirements.txt

Installation
------------

From PyPI
~~~~~~~~~

**Notes**

-  Don't forget to `modify <#configure>`__ **/etc/brocadetool.conf**
   after installation

   ::

       sudo pip install netscaler-tool
       sudo mkdir -p /var/log/brocade-tool
       sudo touch /var/log/brocade-tool/brocade-tool.log
       sudo chown <user>:<group> /var/log/brocade-tool/brocade-tool.log
       sudo chmod <mode> /var/log/brocade-tool/brocade-tool.log
       sudo wget -O /etc/brocadetool.conf https://github.com/tagged/brocade-tool/blob/master/brocadetool.conf.example

From Source
~~~~~~~~~~~

#. git clone https://github.com/tagged/brocade-tool.git
#. cd brocade-tool
#. sudo python setup.py install
#. sudo mkdir -p /var/log/brocade-tool
#. sudo touch /var/log/brocade-tool/brocade-tool.log
#. sudo chown <user>:<group> /var/log/brocade-tool/brocade-tool.log
#. sudo chmod <mode> /var/log/brocade-tool/brocade-tool.log
#. sudo cp brocadetool.conf.example /etc/brocadetool.conf
#. Modify /etc/brocadetool.conf

Configuration
-------------
All changes should be made in /etc/brocadetool.conf

#. Set previous_data_path to the path where brocade-tool where store metric for any OIDs that have rate option set.
#. Set **passwd** with the SNMP community password
#. Set **oids**

   - If you want to turn a counter into a gauge, specify 'rate'
#. (Optional)

   -  Set carbon values, if you plan to send metric to a carbon

Usage
-----

Currently, the brocade-tool is used for monitoring. Enter all the OIDs you want to monitor in the /etc/brocadetool.conf yaml file and that is it.

::

    brocade-tool --help
    usage: brocade-tool [-h] [--passwd PASSWD] [--dryrun] [--debug] [--verbose]
                        [--carbon]
                        BROCADE {show} ...

    positional arguments:
      BROCADE          IP or name of Brocade
      {show}
        show           sub-command for showing objects

    optional arguments:
      -h, --help       show this help message and exit
      --passwd PASSWD  Community password for brocade user. Default is to fetch
                       from brocadetool.conf
      --dryrun         Dryrun
      --debug          Shows what's going on
      --verbose, -v    Shows more info
      --carbon         Send data to carbon?

    brocade-tool brocade01 show --help
    usage: brocade-tool BROCADE show [-h] {ports} ...

    positional arguments:
      {ports}
        ports     sub-command for showing stats about all ports

    optional arguments:
      -h, --help  show this help message and exit

By default, brocade-tool will query the brocade device for all specified
OIDs. If you wish to have it only query a sub set of OIDs, you can use **--stat**

::

    brocade-tool brocade01 show ports --stat swFCPortTxWords swFCPortRxWords