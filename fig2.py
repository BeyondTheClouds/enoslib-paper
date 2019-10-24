# -*- coding: utf-8 -*-

# Imports
import inspect
import scapy.all as scapy

from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.types import Network

from utils import (setup_galera, infra, lookup_net, ifname, Network,
                   LOG)


# Fig Code
def analyze_galera(net: Network):
    '''Fig2. Analyze of the Galera protocol on the `net` Network.

    This function builds a specific `filter` with the CIDR of the
    `net` and prints TCP `packets` that are related to the Galera
    communications.

    '''
    LOG.info(f'Listen packet on {ifname(net)}...')
    scapy.sniff(
        iface=ifname(net), count=10,  # Stop analysis after 10 packets
        filter=f'net {net["cidr"]} and tcp and port 4567',
        prn=lambda packet: packet.summary())


# Test it!

# Define the infrastructure: 2 machines, 1 net
CONF = (Configuration()
        .from_settings(backend="virtualbox")
        .add_machine(flavour="tiny", number=2, roles=["database"])
        .add_network(cidr="192.168.42.0/24", roles=["database"])
        .finalize())

# Setup the infra and call the `analyze_galera` function
with infra(CONF) as (hosts, roles, networks):
    # First, install and configure active/active Galera
    setup_galera(roles, networks)

    # Then, analyze
    LOG.info(inspect.getsource(analyze_galera))
    analyze_galera(lookup_net(networks, "database"))
