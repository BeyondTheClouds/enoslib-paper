# -*- coding: utf-8 -*-


# Imports
import inspect

from enoslib.api import (get_hosts, sync_info)
from enoslib.infra.provider import Provider
from enoslib.infra.enos_vagrant.provider      import Enos_vagrant
from enoslib.infra.enos_vagrant.configuration import Configuration

from enoslib.service.emul.netem import Netem
from enoslib.service.monitoring.monitoring import TIGMonitoring as Monitoring

from utils import (ansible_on, setup_galera, infra,
                   ifname, LOG, populate_ipv4)


# Fig Code
def experiment(provider, conf, delay, setup):
    'Fig2. Artifact for the evaluation of distributed RDBMSes'

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Acquire resources on the testbed")
    infra = provider(conf)
    hosts, networks = infra.init()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Install the distributed RDBMS and third party soft")
    setup(hosts, networks, rdbms_role='RDBMS', sysbench_role='client')
    monitor(hosts, networks, monitored_role='RDBMS', aggregator_role='client[0]')
    LOG.info("Configure the infrastructure")
    set_latency(hosts, networks, delay, role='RDBMS')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Benchmark the distributed RDBMS")
    exec_sysbench(hosts, role='client')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Collect/backup all logs")
    with ansible_on(hosts, role='all') as playbook:
        playbook.archive(path='/var/log', dest='/var/log.tar.gz')
        playbook.fetch(src='/var/log.tar.gz', dest='/tmp/log-{{inventory_hostname}}')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    LOG.info("Clean resources")
    infra.destroy()



# Utils
def monitor(hosts, networks, monitored_role, aggregator_role):

    '''Install monitoring stack.

    This function uses enoslib Monitoring service
    '''
    hosts = populate_ipv4(hosts, networks, "monitor") # Required to use monitor net
    host_ui = get_hosts(hosts, aggregator_role)[0]
    m = Monitoring(collector=get_hosts(hosts, aggregator_role)[0],
                   agent=get_hosts(hosts, monitored_role),
                   ui=host_ui,
                   networks=networks['monitor'])
    m.deploy()

    # Display UI URLs to view metrics
    LOG.info(f'View Monitoring UI at http://{host_ui.extra["monitor_ipv4"]}:3000')
    LOG.info('Connect with `admin` as login and password. '
             'Skip the change password. '
             'Select `Host Dashboard`.')


def set_latency(hosts, networks, delay, role):
    '''Set latency between nodes

    This function uses enoslib SimpleNetem service
    '''
    hosts = sync_info(hosts, networks) # Required to use RDBMS net
    netem = Netem(f"delay {delay}", hosts=hosts[role], networks=networks[role])
    netem.deploy()
    netem.validate()  # Ensure latency is set as expected

def exec_sysbench(hosts, role):
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
