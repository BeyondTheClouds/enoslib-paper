# -*- coding: utf-8 -*-

# Imports
import inspect
import json

from enoslib.api import play_on, discover_networks
from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.types import Network, Roles

from utils import infra, List, LOG


# Fig Code
def monitor(rs: Roles, nets: List[Network]):
    '''Fig4. Reusable function for monitoring.

    Collect metrics on `monitored` hosts. Store and see metrics on
    `aggregator` hosts. Use the `monitor` network to send metrics.

    '''
    # Discover networks to use net info in telegraf.conf.j2
    discover_networks(rs, nets)

    # Install Docker
    with play_on(pattern_hosts="all", roles=rs) as ansible:
        ansible.shell(
            "which docker || (curl -sSL https://get.docker.com/ | sh)",
            display_name="Install docker")
        ansible.apt(
            display_name="Install python-docker (for ansible docker_container)",
            name="python-docker", update_cache=True)

    # Install Telegraf on monitored machines
    with play_on(pattern_hosts="monitored", roles=rs, gather_facts="all") as ansible:
        ansible.template(
            display_name="Generating Telegraf conf",
            src="ansible/telegraf.conf.j2",
            dest="/root/telegraf.conf")
        ansible.docker_container(
            display_name="Installing Telegraf",
            name="telegraf", image="telegraf:1.12-alpine",
            detach=True, network_mode="host", state="started",
            volumes=['/root/telegraf.conf:/etc/telegraf/telegraf.conf'])

    # Install InfluxDB and Grafana on `aggregator` machines
    with play_on(pattern_hosts="aggregator", roles=rs) as ansible:
        ansible.docker_container(
            display_name="Install InfluxDB",
            name="influxdb", image="influxdb:1.7-alpine",
            detach=True, state="started", network_mode="host",
            exposed_ports="8086:8086")
        ansible.wait_for(
            display_name="Waiting for InfluxDB to be ready",
            host="localhost", port="8086", state="started",
            delay=2, timeout=120,)

        ansible.docker_container(
            display_name="Install Grafana",
            name="grafana", image="grafana/grafana:5.4.3",
            detach=True, state="started", network_mode="host",
            exposed_ports="3000:3000")
        ansible.wait_for(
            display_name="Waiting for Grafana to be ready",
            host="localhost", port="3000", state="started",
            delay=2, timeout=120,)
        ansible.uri(
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
        ansible.uri(
            display_name="Import dashboard in Grafana",
            url="http://localhost:3000/api/dashboards/import",
            user="admin", password="admin", force_basic_auth=True,
            body_format="json", method="POST",
            status_code=[200], # 409 for already added
            src="ansible/grafana-dashboard.json")

    # Display UI URLs to view metrics
    ui_urls = map(lambda h: f'http://{h.extra["monitor_ip"]}:3000', rs['aggregator'])
    LOG.info(f'View UI on {list(ui_urls)}')
    LOG.info('Connect with `admin` as login and password, '
             'then skip the change password, '
             'and finally select `Host Dashboard`.')


# Test it!

# Define the infrastructure: 2 database/monitored machines, 2
# database/client/monitored machines, 1 aggregator machine, 1 net for
# database, 1 net for monitoring.
CONF = (Configuration()
        .from_settings(backend="virtualbox")
        .add_machine(flavour='tiny', number=2, roles=['database', 'monitored'])
        .add_machine(flavour='tiny', number=2, roles=['database', 'client', 'monitored'])
        .add_machine(flavour='tiny', number=1, roles=['aggregator'])
        .add_network(cidr='192.168.42.0/24', roles=['database'])
        .add_network(cidr='192.168.43.0/24', roles=['monitor'])
        .finalize())

# Setup the infra and call the `monitor` function
with infra(CONF) as (_, roles, networks):
    LOG.info(inspect.getsource(monitor))
    monitor(roles, networks)
