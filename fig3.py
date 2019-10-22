# -*- coding: utf-8 -*-

# Imports/Type defs
from enoslib.api import run_command

from utils import infra, Roles, LOG


# Code snippet
def contextualize(rs: Roles):
    run_command("apt install -y mariadb-server galera",
                pattern_hosts="database",
                roles=rs)
    run_command("curl -s https://packagecloud.io/install/repositories/akopytov/sysbench/script.deb.sh | bash; apt install -y sysbench",
                pattern_hosts="client",
                roles=rs)


if __name__ == '__main__':
    with infra() as (_, roles, _):
        LOG.info("Contextualize...")
        contextualize(roles)
        LOG.info("Finished!")
