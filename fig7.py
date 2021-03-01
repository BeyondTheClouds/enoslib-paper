# -*- coding: utf-8 -*-

# Imports
import inspect
import json

from enoslib.api import ensure_python3
from enoslib.infra.enos_vagrant.configuration import Configuration

from utils import infra, LOG, ansible_on, populate_ipv4


# Fig Code
def monitor(hosts, nets, monitored_role, aggregator_role):
    '''Fig7. Reusable function for monitoring.

    Collect metrics on `monitored` hosts. Store and see metrics on
    `aggregator` hosts. Use the `monitor` network to send metrics.

    '''
    # Discover networks to use net info in telegraf.conf.j2
    # plus ensure python3 is installed on machines
    hosts = populate_ipv4(hosts, nets, "monitor")
    ensure_python3(make_default=True, roles=hosts)

    # Install Docker
    with ansible_on(hosts, role="all") as playbook:
        playbook.shell(
            "which docker || (curl -sSL https://get.docker.com/ | sh)",
            display_name="Install docker")
        playbook.pip(
            display_name="Install python docker (for ansible docker_container)",
            name="docker[tls]==4.3.1")

    # Install Telegraf on monitored machines
    with ansible_on(hosts, role=monitored_role) as playbook:
        playbook.template(
            display_name="Generating Telegraf conf",
            src="misc/telegraf.conf.j2",
            dest="/root/telegraf.conf")
        playbook.docker_container(
            display_name="Installing Telegraf",
            name="telegraf", image="telegraf:1.12-alpine",
            detach=True, network_mode="host", state="started",
            volumes=['/root/telegraf.conf:/etc/telegraf/telegraf.conf'])

    # Install InfluxDB and Grafana on `aggregator` machines
    with ansible_on(hosts, role=aggregator_role) as playbook:
        playbook.docker_container(
            display_name="Install InfluxDB",
            name="influxdb", image="influxdb:1.7-alpine",
            detach=True, state="started", network_mode="host",
            exposed_ports="8086:8086")
        playbook.wait_for(
            display_name="Waiting for InfluxDB to be ready",
            host="localhost", port="8086", state="started",
            delay=2, timeout=120,)

        playbook.docker_container(
            display_name="Install Grafana",
            name="grafana", image="grafana/grafana:5.4.3",
            detach=True, state="started", network_mode="host",
            exposed_ports="3000:3000")
        playbook.wait_for(
            display_name="Waiting for Grafana to be ready",
            host="localhost", port="3000", state="started",
            delay=2, timeout=120,)
        playbook.uri(
            display_name="Add InfluxDB in Grafana",
            url="http://localhost:3000/api/datasources",
            user="admin", password="admin", force_basic_auth=True,
            body_format="json", method="POST",
            status_code=[200,409], # 409 for already added
            body=json.dumps({
                "name": "telegraf", "type": "influxdb",
                "url": "http://localhost:8086",
                "access": "proxy", "database": "telegraf",
                "isDefault": True}))
        playbook.uri(
            display_name="Import dashboard in Grafana",
            url="http://localhost:3000/api/dashboards/import",
            user="admin", password="admin", force_basic_auth=True,
            body_format="json", method="POST",
            status_code=[200], # 409 for already added
            src="misc/grafana-dashboard.json")

    # Display UI URLs to view metrics
    ui_urls = map(lambda h: f'http://{h.extra["monitor_ipv4"]}:3000', hosts[aggregator_role])
    LOG.info(f'View UI at {list(ui_urls)}')
    LOG.info('Connect with `admin` as login and password. '
             'Skip the change password. '
             'Select `Host Dashboard`.')


# Test it!

# Define the infrastructure: 2 database/monitored machines, 2
# database/client/monitored machines, 1 aggregator machine, 1 net for
# database, 1 net for monitoring.
CONF = (Configuration()
        .from_settings(backend="virtualbox")
        .add_machine(flavour='tiny', number=2, roles=['RDBMS', 'monitored'])
        .add_machine(flavour='tiny', number=2, roles=['RDBMS', 'client', 'monitored'])
        .add_machine(flavour='tiny', number=1, roles=['aggregator'])
        .add_network(cidr='192.168.43.0/24', roles=['RDBMS'])
        .add_network(cidr='192.168.44.0/24', roles=['monitor'])
        .finalize())

# Setup the infra and call the `monitor` function
with infra(CONF) as (hosts, networks):
    LOG.info(inspect.getsource(monitor))
    monitor(hosts, networks,
            monitored_role='monitored',
            aggregator_role='aggregator')
