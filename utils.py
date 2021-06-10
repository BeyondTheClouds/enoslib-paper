import shutil
import logging
import pathlib
from contextlib import contextmanager
from ipaddress import IPv4Network
from typing import List

import enoslib as elib
from enoslib.api import (ensure_python3, get_hosts, play_on, run_ansible,
    sync_info)
from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from pr2modules.ndb.main import NDB


# General stuff
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('TPDS')


# Utils functions
def setup_galera(
        rdbms: List[elib.Host],
        sysbenchs: List[elib.Host],
        rdbms_nets: List[elib.Network]):
    '''Installs and configures Galera.

    This function uses an ansible playbook at `misc/deploy-galera.yml`
    to deploy and configure Galera.
    '''
    galera_ansible_path = 'misc/deploy-galera.yml'

    # Get network information and put RDBMS IP into host.extra so they
    # will be passed to Ansible as host_vars.
    hosts = populate_ipv4({'RDBMS': rdbms, 'client': sysbenchs},
                          {'RDBMS': rdbms_nets}, "RDBMS")

    ensure_python3(make_default=True, roles=hosts)
    run_ansible([galera_ansible_path], roles=hosts)


@contextmanager
def ansible_on(hosts: elib.Roles, role: str):
    with play_on(roles=hosts, pattern_hosts=role, gather_facts="all") as playbook:
        yield playbook


@contextmanager
def infra(conf: Configuration):
    'Provision and remove a `conf` infrastructure from Vagrant.'

    # Get the Vagrant provider
    vagrant_provider = Enos_vagrant(conf)

    # Setup the infra
    LOG.info("Provisioning machines...")
    hosts, networks = vagrant_provider.init()

    LOG.info("Provisioning finished")

    try:
        # Let the user does it stuff
        # yield: Tuple[Roles, List[Network]]
        yield hosts, networks

        LOG.info('You can SSH on Hosts from another terminal with:')
        for host in get_hosts(roles=hosts, pattern_hosts='all'):
            LOG.info(f'- vagrant ssh {host.alias}')

        input('Press Enter to finish...')
    except Exception as e:
        LOG.error(f'Unexpected error: {e}')
    finally:
        pass
        # # Tear down the infra
        # LOG.info('Finished!')
        # LOG.info('Destroying machines...')
        # vagrant_provider.destroy()

        # tmp_enoslib_path = pathlib.Path('_tmp_enos_')
        # LOG.info(f'Removing cache {tmp_enoslib_path}...')
        # if tmp_enoslib_path.is_dir():
        #     shutil.rmtree(tmp_enoslib_path)


def ifname(net: IPv4Network) -> str:
    'Returns ifname of net/cidr on the current machine'
    ndb = NDB()
    cidr = net.with_prefixlen  # 192.168.42.0/24
    cidr_route = ndb.routes[cidr]
    addr_route = f'{cidr_route["prefsrc"]}/{cidr_route["dst_len"]}'
    ifname = ndb.addresses[addr_route]['label']
    ndb.close()

    return ifname

def populate_ipv4(hosts: elib.Roles, nets: elib.Networks, net_role):
    '''Discover network info and put it into host.extra so it will be
    passed to Ansible as host_vars.

    The ipv4 will be available in ansible with the idiom
    `{{ hostvars[h][net_role + '_ipv4'] }}`
    '''
    hosts = elib.sync_info(hosts, nets)

    for hs in hosts.values():
        for h in hs:
            net_role_ip = next( format(addr.ip.ip) for addr in h.filter_addresses(nets[net_role])
                                                   if addr.ip.version == 4)
            h.extra.update({net_role + '_ipv4': net_role_ip})

    return hosts
