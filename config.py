"""Configuration.
We often make several experiments with a model and "tune"
parameters, either to refine it or to better understand
what the affect is of changing assumptions ("sensitivity analysis").
We could do this by changing Python code, but to the extent possible
it's better to separate out the parameters.  For this we typically
read a separate configuration file.
"""

import configparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

CONF = None

def configure(filename: str):
    global CONF
    CONF = configparser.ConfigParser(inline_comment_prefixes="#")
    log.info(f"Configuring from file {filename}")
    CONF.read_file(open(filename))

def get_float(section: str, parameter: str) -> float:
    assert CONF, "Must call configure first"
    param_str = CONF[section][parameter]
    return float(param_str)

def get_int(section: str, parameter: str) -> int:
    assert CONF, "Must call configure first"
    param_str = CONF[section][parameter]
    return int(param_str)

def get_pcnt(section: str, parameter: str) -> float:
    """Interpret integer as fraction of 100"""
    assert CONF, "Must call configure first"
    param_str = CONF[section][parameter]
    return float(param_str)/100.0




