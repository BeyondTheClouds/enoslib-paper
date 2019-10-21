# -*- coding: utf-8 -*-

# Imports/Type defs
from typing import List

from enoslib.host import Host
from enoslib.api import run as run_command

from utils import infra, LOG


# Code snippet
def contextualize(hosts: List[Host]):
    run_command("apt install -y mariadb-server galera", hosts)


# Test it!
with infra() as (hosts, _, _):
    LOG.info("Contextualize...")
    contextualize(hosts)
    LOG.info("Finished!")
