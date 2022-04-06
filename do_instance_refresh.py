# read from the config file
import json
import logging
import os
from slack.Slack import SlackAPI

from utils.utils import (create_new_launch_configuration, get_asg_name, update_asg_with_new_lc,
                          check_instance_refresh_status)

from check_ami_version import boto3_clients


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# temp file location , which can be reused across a pipeline run
TEMP_FILE_PATH = '/tmp/services.state.json'

slack = SlackAPI(os.getenv('WEBHOOK_URL'))

with open(TEMP_FILE_PATH,'r') as fp:
    config = json.load(fp)

cache_boto3_clients = []


def error_fn(**kwargs):
    slack.send_simple_message(f'{kwargs["asg_name"]} Failed.\n{kwargs["message"]}')


def success_fn(**kwargs):
    slack.send_simple_message(f'{kwargs["asg_name"]} Success.\n{kwargs["message"]}')


for each_service in config:
    if config[each_service]['AMI_CHANGED']:
        for each_region in config[each_service]:
            if each_region != 'AMI_CHANGED':
                # read the config
                new_ami_id = config[each_service][each_region]['LATEST_AMI_ID']
                ec2_client = boto3_clients[each_region]['EC2']
                asg_client =  autoscaling_client = boto3_clients[each_region]['AUTOSCALING']
                lc_config =  config[each_service][each_region]['LAUNCH_CONFIG']
                asg_name_prefix =  config[each_service][each_region]['ASG_NAME']

                asg_name =  get_asg_name(asg_client,asg_name_prefix)

                instance_refresh_config  = config[each_service][each_region]['INSTANCE_REFRESH_CONFIG']
                
                logger.info(f'Action Required: New Launch Configuration for service {each_service} , region {each_region}.')

                # create new lc
                new_lc_name = create_new_launch_configuration(asg_client,lc_config,new_ami_id)
                
                # new_lt_id = create_new_launch_template(ec2_client,lc_config,new_ami_id)
                if new_lc_name is not None:
                    logger.info(f'New Launch Configuration  for service {each_service} , region {each_region} is {new_lc_name}')

                    # start instance refresh with the latest lt id
                    instance_refresh_id = update_asg_with_new_lc(asg_client,asg_name,new_lc_name,instance_refresh_config)
                    logger.info(f'Instance Refresh({instance_refresh_id})started for service {each_service} , region {each_region}.')
                    # check the status until it is successful or failed
                    check_instance_refresh_status(asg_client,asg_name,instance_refresh_id,{'errorFn': error_fn,'successFn':success_fn})

    else:
        logger.info(f'No Action Required: As Instances are using latest ami for service {each_service}')     
