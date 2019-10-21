# -*- coding: utf-8 -*-

# Imports/Type defs
import scapy.all as scapy

from utils import infra, Network, LOG
from fig1 import contextualize


# Code snippet
def analyze_galera(net: Network):
    scapy.sniff(
        filter=f'net {net["cidr"]} and tcp and port 4567',
        prn=lambda packet: packet.summary())


# Test it!
with infra() as (hosts, network, _):
    contextualize(hosts)
    LOG.info("Analyze Galera Protocol...")
    analyze_galera(network)
