# -*- coding: utf-8 -*-

# Imports/Type defs
from enoslib.task import enostask
from enoslib.host import Host
from execo_engine import ParamSweeper, sweep

import traceback
from pathlib import Path


@enostask(new=True)
def deploy(env=None):
    roles, networks = {"role1": Host("1.2.3.4")}, []
    # Save the roles and networks in the environment
    env["roles"] = roles
    env["networks"] = networks


@enostask()
def bench(parameter, env=None):
    LOG.info(f"Running bench with {parameter} on {env['roles']}")


@enostask()
def backup(env=None):
    LOG.info(f"Running backup on {env['roles']}")


@enostask()
def destroy(env=None):
    LOG.info(f"Running destroy on {env['roles']}")


# Iterate over a set of parameters
parameters = {"param1": [1, 4], "param2": ["a", "b"]}
sweeps = sweep(parameters)
sweeper = ParamSweeper(persistence_dir=str(Path("sweeps")),
                       sweeps=sweeps, 
                       save_sweeps=True)      
parameter = sweeper.get_next()
while parameter:
    try:
       deploy(); 
       bench(parameter); 
       backup(); 
       sweeper.done(parameter)
    except Exception as e:
        traceback.print_exc()
        sweeper.skip(parameter)
    finally:
        destroy()
        parameter = sweeper.get_next()