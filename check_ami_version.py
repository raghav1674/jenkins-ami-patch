#!/usr/bin/python3
import json
import logging
from collections import OrderedDict

from os import getenv
from utils.load_config import DateTimeEncoder, get_config
from utils.utils import (get_latest_ami_version,
                         get_service_ami_version_from_lc,
                         compare_ami_versions,
                         prepare_boto_clients
                         )

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# temp file location , which can be reused across a pipeline run
TEMP_STATE_FILE_PATH = '/tmp/services.state.json'

# config file path
CONFIG_FILE_PATH = getenv(
    'AWS_SERVICE_CONFIG_FILE') or './config/config.yaml' # config file path


config = get_config(CONFIG_FILE_PATH)  # load the config
regions = config['regions']  # get the regions
# get the boto3 service client names , e.g. ec2
boto3_client_services = config['aws_boto_clients']

services = config['services']

boto3_clients = prepare_boto_clients(boto3_client_services, regions)

# check the ami versions
def check_ami_versions():

    global services
    global boto3_client_services
    global regions
    global config
    global boto3_clients

    status_map = OrderedDict()


    for each_service in services:

        svc_name = each_service
        matched = True
        # getting the ami filters
        filters = services[each_service]['Properties']['ami_filters']
        # launch config name
        lc_name = services[each_service]['Properties']['launch_config_name']

        # instance refresh config
        instance_refresh_config = services[each_service]['Properties']['instance_refresh_config']
        asg_name_prefix = services[each_service]['Properties']['asg_name']

        status_map[svc_name] = {
            'TEST_JOBS':services[each_service]['Properties']['test_jobs'],
        }

        for each_region in services[each_service]['Properties']['regions']:

            status_map[svc_name][each_region] = {}

            # boto3 service clients
            ec2_client = boto3_clients[each_region]['EC2']
            autoscaling_client = boto3_clients[each_region]['AUTOSCALING']

            # first get the latest ami version
            latest_ami_id = get_latest_ami_version(ec2_client, filters)

            launch_config = get_service_ami_version_from_lc(
                autoscaling_client, lc_name)

            launch_config_ami_id = launch_config and launch_config['ImageId']
                        
            # if ami id and launch config ami id is not None
            if latest_ami_id and launch_config_ami_id:
                # if ami id matches
                if compare_ami_versions(latest_ami_id, launch_config_ami_id):
                    matched =  matched and True
                   
                else:
                    matched = False
            else:
                matched = None
 
        
            # store the output
            status_map[svc_name][each_region] = {

                'LATEST_AMI_ID': latest_ami_id,
                'LAUNCH_CONFIG_AMI_ID': launch_config_ami_id,
                'MATCHED': matched,
                'LAUNCH_CONFIG': launch_config,
                'ASG_NAME': asg_name_prefix,
                'INSTANCE_REFRESH_CONFIG': instance_refresh_config,
            }

        if matched is not None:
            status_map[svc_name]['AMI_CHANGED'] = not matched
            if matched is True:
                # launch config ami id
                logger.info(f'No Action Required for {svc_name}: , The latest ami id({latest_ami_id}) and currently used ami({launch_config_ami_id}) is same for service {svc_name}')
            else:
                logger.info(f'Action Required for {svc_name}:  The latest ami id({latest_ami_id}) and currently used ami({launch_config_ami_id}) does not matches for service {svc_name}')
        else:
            status_map[svc_name]['AMI_CHANGED'] = False 


    with open(TEMP_STATE_FILE_PATH,'w') as fp:
        json.dump(status_map,fp,indent=4,cls=DateTimeEncoder)

    return status_map

if __name__ == '__main__':   
    print(check_ami_versions())
