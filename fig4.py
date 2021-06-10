# -*- coding: utf-8 -*-

# Imports
import inspect
from typing import List

import enoslib as elib
from enoslib.infra.enos_vagrant.configuration import Configuration

from utils import infra, LOG


# Fig Code
def setup_galera(rdbms: List[elib.Host], sysbenchs: List[elib.Host]):
    '''Fig4. Install MariaDB and Galera on `rdbms` and Sysbench on `sysbenchs`

    `rdbms` and `sysbenchs` are list of `Host`.  A `Host` is an abstract notion
    of unit of computation that can be bound to bare-metal machines, virtual
    machines or containers.

    '''
    # Install the MariaDB Galera cluster on `rdbms`
    elib.run('apt update; apt install -y mariadb-server galera', rdbms)

    # Install Sysbench on `sysbnechs`
    apt_pkg="https://packagecloud.io/install/repositories/akopytov/sysbench/script.deb.sh"
    elib.run(f"curl -s {apt_pkg} | bash; apt install -y sysbench", sysbenchs)

    # Configure sysbench for MariaDB Galera cluster
    # ...


# Test it!

# Define the infrastructure: 4 machines
CONF = (Configuration()
        .from_settings(backend="virtualbox")
        .add_machine(flavour="tiny", number=2, roles=["RDBMS"])
        .add_machine(flavour="tiny", number=2, roles=["RDBMS", "client"])
        .finalize())

# Setup the infra and call the `setup_galera` function
with infra(CONF) as (hosts, _):
    LOG.info(inspect.getsource(setup_galera))
    setup_galera(rdbms=hosts["RDBMS"], sysbenchs=hosts["client"])
