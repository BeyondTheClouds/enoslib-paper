from contextlib import contextmanager
import logging
from typing import Tuple, List, Dict

from enoslib.host import Host
from enoslib.api import play_on
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.infra.enos_vagrant.configuration import Configuration


# General stuff
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('IPDPS')


# Type definitions
Network = Dict[str, str]
Roles = Dict[str, List[Host]]


# Utils functions
def setup_galera():
    '''Installs and configures Galera'''
    _, network, rs = make_infra()
    with play_on("database", roles=rs) as ansible:
        ansible.apt(name=["mariadb-server", "galera"], state="present")

@contextmanager
def infra():
    '''Provision and remove an infrastructure from Vagrant VirtualBox.

    '''
    # Configuration for database and client machines
    CONF = (Configuration()
            .add_machine(flavour="tiny", number=2, roles=["database"])
            .add_machine(flavour="tiny", number=2, roles=["database", "client"])
            .add_network(cidr="192.168.42.0/24", roles=["database"])
            .finalize())

    # Get the Vagrant provider
    vagrant_provider = Enos_vagrant(CONF)

    # Setup the infra
    LOG.info("Provisioning machines...")
    roles, networks = vagrant_provider.init()

    # Compute the list of Hosts
    hosts = set([h for hs in roles.values()
                   for h  in hs])

    try:
        # Let the user does it stuff
        # yield: Tuple[List[Host], List[Network], Roles]
        yield hosts, networks[0], roles
    except Exception as e:
        LOG.error(f"Unexpected error: {e}")
    finally:
        # Tear down the infra
        LOG.info("Destroying machines...")
        # vagrant_provider.destroy()
