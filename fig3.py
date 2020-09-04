# -*- coding: utf-8 -*-

# Imports
import os
from pprint import pformat
import yaml

from enoslib.infra.enos_vagrant.configuration import Configuration

from utils import infra, LOG


# Fig Code (Load the yaml file)
YAML_PATH = '5rdbms2sys-vagrant.yaml'
YAML_DICT = None
with open(YAML_PATH) as yaml_file:
    YAML_DICT = yaml.safe_load(yaml_file)


# Test It!

# Define the infrastructure: 2 database machines, 2
# database/client machines, 1 net
CONF = Configuration.from_dictionnary(YAML_DICT)

# Setup the infra and call the `contextualize` function
LOG.info(f'Provisionning of {YAML_PATH}:\n{pformat(CONF.to_dict())}')
with infra(CONF):
    pass
