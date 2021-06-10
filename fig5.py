# -*- coding: utf-8 -*-


# Imports
import inspect
from typing import List

import scapy.all as scapy
from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.objects import Network
from scapy.config import conf as scapy_config
from utils import LOG, ifname, infra, setup_galera


scapy_config.use_pcap = True


# Fig Code
def analyze_galera(nets: List[Network]):
    '''Fig5. Analyze of the Galera protocol on the `net` Network.

    This function builds a specific `filter` with the CIDR of the
    `net` and prints TCP `packets` that are related to the Galera
    communications.

    '''
    net_ipv4 = next(net.network for net in nets if net.network.version == 4)

    LOG.info(f"Listening the 10 Galera packets on {ifname(net_ipv4)}...")
    scapy.sniff(
        iface=ifname(net_ipv4), count=10,  # Stop analysis after 10 packets
        filter=f'net {net_ipv4.with_prefixlen} and tcp and port 4567',
        prn=lambda packet: packet.summary())


# Test it!

# Define the infrastructure: 2 machines, 1 net
CONF = (Configuration()
        .from_settings(backend="libvirt")
        .add_machine(flavour="tiny", number=2, roles=["RDBMS"])
        .add_network(cidr="192.168.42.0/24", roles=["RDBMS"])
        .finalize())

# Setup the infra and call the `analyze_galera` function
with infra(CONF) as (hosts, networks):
    # First, install and configure active/active Galera
    setup_galera(hosts['RDBMS'], [], networks['RDBMS'])

    # Then, analyze
    LOG.info(inspect.getsource(analyze_galera))
    analyze_galera(networks["RDBMS"])
