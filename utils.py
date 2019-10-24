from contextlib import contextmanager
from functools import wraps
import logging
import os
import shutil
from typing import List

from pyroute2 import NDB
from pyroute2 import log as pyroute2log

from enoslib.host import Host
from enoslib.api import (play_on, run_ansible, generate_inventory,
                         gather_facts, discover_networks)
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.types import Network, Role, Roles


# General stuff
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('IPDPS')


# Utils functions
def setup_galera(rs: Roles, nets: List[Network]):
    '''Installs and configures Galera'''
    galera_ansible_path = 'ansible/deploy-galera.yml'

    discover_networks(rs, nets)
    run_ansible([galera_ansible_path], roles=rs)


@contextmanager
def infra(conf: Configuration):
    'Provision and remove a `conf` infrastructure from Vagrant.'

    # Get the Vagrant provider
    vagrant_provider = Enos_vagrant(conf)

    # Setup the infra
    LOG.info("Provisioning machines...")
    roles, networks = vagrant_provider.init()

    # Extract the list of Hosts from Roles
    hosts = set([h for hs in roles.values()
                   for h  in hs])

    try:
        # Let the user does it stuff
        # yield: Tuple[List[Host], Roles, List[Network]]
        yield hosts, roles, networks

        LOG.info('You can SSH on Hosts from another terminal with:')
        for h in hosts:
            LOG.info(f'- vagrant ssh {h.alias}')

        input('Press Enter to finish...')
    except Exception as e:
        LOG.error(f'Unexpected error: {e}')
    finally:
        # Tear down the infra
        LOG.info('Finished!')
        LOG.info('Destroying machines...')
        vagrant_provider.destroy()

        tmp_enoslib_path = '_tmp_enos_'
        LOG.info(f'Removing cache {tmp_enoslib_path}...')
        if os.path.isdir(tmp_enoslib_path):
            shutil.rmtree(tmp_enoslib_path)


def lookup_net(nets: List[Network], r: Role) -> Network:
    'Returns the first Network with the Role `r`'
    for net in nets:
        if r in net.get("roles", []):
            return net

    raise LookupError(f'Missing network with role {r}')


def ifname(net: Network) -> str:
    'Returns ifname of net["cidr"] on the current machine'
    ndb = NDB()
    cidr_route = ndb.routes[net["cidr"]]
    addr_route = f'{cidr_route["prefsrc"]}/{cidr_route["dst_len"]}'
    ifname = ndb.addresses[addr_route]['label']
    ndb.close()

    return ifname
