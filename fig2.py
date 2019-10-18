# -*- coding: utf-8 -*-

# Imports/Type defs
from typing import List, Dict

import scapy.all as scapy

from enoslib.host import Host
from enoslib.api import run_command

Network = Dict[str, str]


# Code snippet
def analyze_galera(net: Network):
    scapy.sniff(
        filter=f'net {net["CIDR"]} and tcp and port 4567',
        prn=lambda packet: packet.summary())


# Extra code to execute the `analyze_galera` function on 3 VMs from
# Vagrant VirtualBox
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.infra.enos_vagrant.configuration import Configuration

def contextualize(hosts: List[Host]):
    run_command("apt install -y mariadb galera", hosts)

conf = (Configuration()
        .add_machine(flavour="tiny", number=3, roles=["database"])
        .add_network(cidr="192.168.42.0/24", roles=["database"])
        .finalize())

provider = Enos_vagrant(conf)
roles, networks = provider.init()

# Install Galera first
contextualize(set(roles.values()))

# Analyze then
analyze_galera(networks["database"])
