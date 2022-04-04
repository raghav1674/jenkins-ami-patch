#!/usr/bin/python3
import json
import logging
from os import getenv
from utils.load_config import DateTimeEncoder, get_config
from utils.utils import (get_latest_ami_version, get_latest_launch_template,
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

    status_map = {}


    for each_service in services:

        svc_name = each_service

        matched = True

        # ssm parameter
        ssm_parameter_path = services[each_service]['Properties']['ami_id_ssm_parameter']
        
       
        # launch config name
        lc_name = services[each_service]['Properties']['launch_config_name']

        # instance refresh config
        instance_refresh_config = services[each_service]['Properties']['instance_refresh_config']
        asg_name = services[each_service]['Properties']['asg_name']

        status_map[svc_name] = {}

        for each_region in services[each_service]['Properties']['regions']:

            status_map[svc_name][each_region] = {}

            # boto3 service clients
            ec2_client = boto3_clients[each_region]['EC2']
            autoscaling_client = boto3_clients[each_region]['AUTOSCALING']
            ssm_client = boto3_clients[each_region]['SSM']

            # first get the latest ami version
            latest_ami_id = get_latest_ami_version(ssm_client, ssm_parameter_path)

            # launch config ami id
            logger.info(f'The Latest ami id for service {svc_name} , region {each_region} is {latest_ami_id}')

            # first search if the launch template is present, if present then use that
            launch_config = get_latest_launch_template(ec2_client,lc_name)

            # if lt is not present then search in launch configuration as it might be the first time
            if not launch_config:

                launch_config = get_service_ami_version_from_lc(
                    autoscaling_client, lc_name)

            launch_config_ami_id = launch_config and launch_config['ImageId']
            
            logger.info(f'The ami id currently in use by service {svc_name} , region {each_region} is {launch_config_ami_id}')
            
            # if ami id and launch config ami id is not None
            if latest_ami_id and launch_config_ami_id:
                # if ami id matches
                if compare_ami_versions(latest_ami_id, launch_config_ami_id):
                    matched =  matched and True
                    logger.info(f'No Action Required for {svc_name}: , The latest ami id({latest_ami_id}) and currently used ami({launch_config_ami_id}) is same for service {svc_name} , region {each_region}')
                else:
                    matched = False
                logger.info(f'Action Required for {svc_name}:  The latest ami id({latest_ami_id}) and currently used ami({launch_config_ami_id}) does not matches for service {svc_name} , region {each_region}')
            else:
                matched = None
 
           

            # store the output
            status_map[svc_name][each_region] = {

                'LATEST_AMI_ID': latest_ami_id,
                'LAUNCH_CONFIG_AMI_ID': launch_config_ami_id,
                'MATCHED': matched,
                'LAUNCH_CONFIG': launch_config,
                'ASG_NAME': asg_name,
                'INSTANCE_REFRESH_CONFIG': instance_refresh_config

            }

        if matched is not None:
            status_map[svc_name]['AMI_CHANGED'] = not matched
        else:
            status_map[svc_name]['AMI_CHANGED'] = False 


    with open(TEMP_STATE_FILE_PATH,'w') as fp:
        json.dump(status_map,fp,indent=4,cls=DateTimeEncoder)

    return status_map


# get the result in a compact manner for groovy
# def get_result():

#     result = check_ami_versions()
#     output = ''
#     for service_name, each_service in result.items():
#         output += service_name + \
#             ":" + str(each_service['AMI_CHANGED'])
#         output += ","

#     return output
if __name__ == '__main__':   
    check_ami_versions()
