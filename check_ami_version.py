#!/usr/bin/python3
from os import getenv
from utils.load_config import get_config
from utils.utils import (get_latest_ami_version,
                         get_service_ami_version_from_lc,
                         compare_ami_versions,
                         prepare_boto_clients
                         )


CONFIG_FILE_PATH = getenv(
    'AWS_SERVICE_CONFIG_FILE') or './config/config.yaml' # config file path

# check the ami versions
def check_ami_versions():

    status_map = {}

    config = get_config(CONFIG_FILE_PATH)  # load the config
    regions = config['regions']  # get the regions
    # get the boto3 service client names , e.g. ec2
    boto3_client_services = config['aws_boto_clients']

    services = config['services']

    boto3_clients = prepare_boto_clients(boto3_client_services, regions)

    for each_service in services:

        job_name = each_service['job_name']

        matched = False

        # image filter
        image_filters = each_service['images']['filters']
        # service name to filter launch config
        service_name = each_service['service_name']

        status_map[job_name] = {}

        for each_region in each_service['regions']:

            status_map[job_name][each_region] = {}

            # boto3 service clients
            ec2_client = boto3_clients[each_region]['EC2']
            autoscaling_client = boto3_clients[each_region]['AUTOSCALING']

            # first get the latest ami version
            latest_ami_id = get_latest_ami_version(ec2_client, image_filters)

            # launch config ami id
            launch_config_ami_id = get_service_ami_version_from_lc(
                autoscaling_client, service_name)

            # if ami id and launch config ami id is not None
            if latest_ami_id and launch_config_ami_id:
                # if ami id matches
                if compare_ami_versions(latest_ami_id, launch_config_ami_id):
                    matched = True
                else:
                    matched = False
            else:
                matched = None

            # store the output
            status_map[job_name][each_region] = {

                'LATEST_AMI_ID': latest_ami_id,
                'LAUNCH_CONFIG_AMI_ID': launch_config_ami_id,
                'MATCHED': matched

            }

        print(status_map)

        if matched is not None:
            status_map[job_name]['AMI_CHANGED'] = not matched
        else:
            status_map[job_name]['AMI_CHANGED'] = False 

    return status_map


# get the result in a compact manner for groovy
def get_result():

    result = check_ami_versions()
    output = ''
    for service_name, each_service in result.items():
        output += service_name + \
            ":" + str(each_service['AMI_CHANGED'])
        output += ","

    return output


print(get_result())
