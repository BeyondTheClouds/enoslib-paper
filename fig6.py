# -*- coding: utf-8 -*-

# Imports
import inspect

from enoslib.api import run as run_command
from enoslib.infra.enos_vagrant.configuration import Configuration
from enoslib.types import Roles

from utils import infra, LOG


# Fig Code
def setup_galera(hosts, rdbms_role, sysbench_role):
    'Fig6. Install Galera on `RDBMS`, and Sysbench on `client` hosts.'
    rdbms_hs = hosts[rdbms_role]
    sysbench_hs = hosts[sysbench_role]

    run_command("apt install -y mariadb-server galera", rdbms_hs)
    run_command("curl -s https://packagecloud.io/install/repositories/akopytov/sysbench/script.deb.sh | bash; apt install -y sysbench",
                sysbench_hs)


# Test It!

# Define the infrastructure: 2 database machines, 2
# database/client machines, 1 net
CONF = (Configuration()
        .from_settings(backend="virtualbox")
        .add_machine(flavour="tiny", number=2, roles=["RDBMS"])
        .add_machine(flavour="tiny", number=2, roles=["RDBMS", "client"])
        .finalize())

# Setup the infra and call the `setup_galera` function
with infra(CONF) as (hosts, _):
    LOG.info(inspect.getsource(setup_galera))
    setup_galera(hosts, "RDBMS", "client")
