# -*- coding: utf-8 -*-


# Imports
from typing import List

import enoslib as elib
from enoslib.api import sync_info
from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from utils import LOG, ansible_on, setup_galera


# Fig Code
def experiment(provider, conf, delay, setup):
    'Fig2. Artifact for the evaluation of distributed RDBMSes'

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Acquire resources on the testbed")
    infra = provider(conf)
    hosts, networks = infra.init()
    hosts = sync_info(hosts, networks)  # Retrieve extra info on hosts

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Install the distributed RDBMS and third party soft")
    setup(hosts['RDBMS'], hosts['client'], networks['RDBMS'])
    monitor(hosts['RDBMS'], hosts['RDBMS'][0], networks['monitor'])
    LOG.info("Configure the infrastructure")
    set_latency(hosts['RDBMS'], networks['RDBMS'], delay)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Benchmark the distributed RDBMS")
    exec_sysbench(hosts['client'])

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Collect/backup all logs")
    with ansible_on(hosts, role='all') as playbook:
        playbook.archive(path='/var/log', dest='/var/log.tar.gz')
        playbook.fetch(src='/var/log.tar.gz', dest='/tmp/log-{{inventory_hostname}}')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Clean resources")
    infra.destroy()



# Utils
def monitor(monitored: List[elib.Host],
            aggregator: elib.Host,
            networks: List[elib.Network],):

    '''Install monitoring stack.

    This function uses enoslib Monitoring service
    '''
    host_ui = aggregator
    m = elib.TIGMonitoring(agent=monitored,
                           collector=aggregator,
                           ui=aggregator,
                           networks=networks)
    m.deploy()

    # Display UI URLs to view metrics
    ui_addr = next(net.ip for net in host_ui.filter_addresses(networks) if net.ip.version == 4)
    LOG.info(f'View Monitoring UI at http://{ui_addr.ip}:3000')
    LOG.info('Connect with `admin` as login and password. '
             'Skip the change password. '
             'Select `Host Dashboard`.')


def set_latency(hs: List[elib.Host], ns: List[elib.Network], delay: str):
    '''Set latency between nodes

    This function uses enoslib SimpleNetem service
    '''
    # hosts = sync_info(hosts, networks) # Required to use RDBMS net
    netem = (elib.Netem()
             .add_constraints(f"delay {delay}", hosts=hs, networks=ns, symetric=True))
    netem.deploy()
    netem.validate()  # Ensure latency is set as expected

def exec_sysbench(hs: List[elib.Host]):
    pass


# Test it!

# Define the infrastructure: 2 machines for RDBMS, 2 machines for
# RDBMS/Client, 1 network for RDBMS, 1 network for monitoring.
CONF = (Configuration()
        .from_settings(backend='virtualbox')
        .add_machine(flavour='tiny', number=2, roles=['RDBMS'])
        .add_machine(flavour='tiny', number=2, roles=['RDBMS', 'client'])
        .add_network(cidr='192.168.43.0/24',   roles=['RDBMS'])
        .add_network(cidr='192.168.44.0/24',   roles=['monitor'])
        .finalize())

experiment(Enos_vagrant, CONF, "10ms", setup_galera)
