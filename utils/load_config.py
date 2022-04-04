#!/usr/bin/python3

from yaml import safe_load
from datetime import datetime
import json


def get_config(config_file_path):
    '''
    @purpose: load the configuration from the file

    @input: config_file_path: str 

    @returns: config_data

    '''

    with open(config_file_path) as fp:
        config_data = safe_load(fp)
    return config_data


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)