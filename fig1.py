# -*- coding: utf-8 -*-

# Imports
import inspect
from typing import List

from enoslib.host import Host
from enoslib.api import run as run_command
from enoslib.infra.enos_vagrant.configuration import Configuration

from utils import infra, LOG


# Fig Code
def contextualize(hosts: List[Host]):
    '''Fig1. Install MariaDB and Galera on a list of `hosts`.

    A `Host` is an abstract notion of unit of computation that can be
    bound to bare-metal machines, virtual machines or containers.

    '''
    run_command("apt install -y mariadb-server galera", hosts)


# Test it!

# Define the infrastructure: 2 machines
CONF = (Configuration()
        .from_settings(backend="virtualbox")
        .add_machine(flavour="tiny", number=2, roles=["database"])
        .finalize())

# Setup the infra and call the `contextualize` function
with infra(CONF) as (hosts, _, _):
    LOG.info(inspect.getsource(contextualize))
    contextualize(hosts)
