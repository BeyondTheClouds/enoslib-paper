# -*- coding: utf-8 -*-

# Imports/Type defs
import scapy.all as scapy

from utils import (setup_galera, infra, lookup_net, ifname, Network,
                   LOG)


# Code snippet
def analyze_galera(net: Network):
    # Sniff packet of Galera (stop after 10 packets)
    scapy.sniff(
        iface=ifname(net), count=10,
        filter=f'net {net["cidr"]} and tcp and port 4567',
        prn=lambda packet: packet.summary())


# Test it!
if __name__ == '__main__':

    with infra() as (_, roles, networks):
        # First, install and configure active/active Galera
        setup_galera(roles, networks)

        # Then, analyze
        LOG.info("Analyzing Galera Protocol...")
        analyze_galera(lookup_net(networks, "database"))
