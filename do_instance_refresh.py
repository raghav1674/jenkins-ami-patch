# read from the config file
import json
import logging


from utils.utils import (update_asg_with_new_lt,
                          create_new_launch_template,
                          check_instance_refresh_status)

from check_ami_version import boto3_clients,regions


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# temp file location , which can be reused across a pipeline run
TEMP_FILE_PATH = '/tmp/services.state.json'

with open(TEMP_FILE_PATH,'r') as fp:
    config = json.load(fp)

cache_boto3_clients = []


for each_service in config:
    if config[each_service]['AMI_CHANGED']:
        for each_region in config[each_service]:
            if each_region != 'AMI_CHANGED':
                # read the config
                new_ami_id = config[each_service][each_region]['LATEST_AMI_ID']
                ec2_client = boto3_clients[each_region]['EC2']
                asg_client =  autoscaling_client = boto3_clients[each_region]['AUTOSCALING']
                lc_config =  config[each_service][each_region]['LAUNCH_CONFIG']
                asg_name =  config[each_service][each_region]['ASG_NAME']
                instance_refresh_config  = config[each_service][each_region]['INSTANCE_REFRESH_CONFIG']
                
                logger.info(f'Action Required: New Launch template/ launch template version for service {each_service} , region {each_region}.')

                # create new lt
                new_lt_id = create_new_launch_template(ec2_client,lc_config,new_ami_id)
                if new_lt_id is not None:
                    logger.info(f'New Launch template/ launch template version for service {each_service} , region {each_region} is {new_lt_id}')

                    # start instance refresh with the latest lt id
                    instance_refresh_id = update_asg_with_new_lt(asg_client,asg_name,new_lt_id,instance_refresh_config)
                    logger.info(f'Instance Refresh({instance_refresh_id})started for service {each_service} , region {each_region}.')
                    # check the status until it is successful or failed
                    check_instance_refresh_status(asg_client,asg_name,instance_refresh_id)

                
