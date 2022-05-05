# read from the config file
import json
import logging
import os
from slack.Slack import SlackAPI
from utils.jenkins_utils import JenkinsApi

from utils.utils import (create_new_launch_configuration, get_asg_name, update_asg_with_new_lc,
                          check_instance_refresh_status)

from check_ami_version import boto3_clients


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# temp file location , which can be reused across a pipeline run
TEMP_FILE_PATH = '/tmp/services.state.json'

slack = SlackAPI(os.getenv('WEBHOOK_URL'))
jenkins_instance = JenkinsApi(os.getenv('JENKINS_URL') ,os.getenv('JENKINS_USERNAME'),os.getenv('JENKINS_TOKEN'))

def error_fn(**kwargs):
    slack.send_simple_message(f'{kwargs["asg_name"]} Failed.\n{kwargs["message"]}')


def success_fn(**kwargs):
    slack.send_simple_message(f'{kwargs["asg_name"]} Success.\n{kwargs["message"]}')

def do_instance_refresh():

    with open(TEMP_FILE_PATH,'r') as fp:
        config = json.load(fp)
    

    service_status = {
        'SERVICES': {}
    }
    

    for each_service in config:
        service_status['SERVICES'][each_service] = False 
        try:
            if not config[each_service]['AMI_CHANGED']:
                total_refresh = 0
                successful_refresh = 0
                for each_region in config[each_service]:
                    if each_region != 'AMI_CHANGED' and each_region!= 'TEST_JOBS':
                        # read the config
                        new_ami_id = config[each_service][each_region]['LATEST_AMI_ID']
                        asg_client =  boto3_clients[each_region]['AUTOSCALING']
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
                            instance_refresh_status = check_instance_refresh_status(asg_client,asg_name,instance_refresh_id,{'errorFn': error_fn,'successFn':success_fn})
                            if instance_refresh_status == 'SUCCESS':
                                successful_refresh += 1
                            total_refresh += 1
                if total_refresh == successful_refresh:
                    logger.info(f'{each_service} is successfully refreshed, running the test jobs....')
                    successful_job_count = 0
                    for each_job in config[each_service]['TEST_JOBS']:
                        response =  jenkins_instance.run_job(each_job)
                        if response is None:
                            logger.error(f'Job {each_job} for service {each_service} failed')
                        else:
                            successful_job_count += 1
                            logger.info(f'Job {each_job} for service {each_service} passed')
                    if successful_job_count == len(config[each_service]['TEST_JOBS']):
                        service_status['SERVICES'][each_service] = True 
                else:
                    logger.warning('f{each_service} , instance refresh not successful')

            else:
                logger.info(f'No Action Required: As Instances are using latest ami for service {each_service}')     
        except Exception as e:
            logger.error(f'{each_service} failed due to the following error: {e}')

    with open(TEMP_FILE_PATH,'a') as ap:
        json.dump(service_status,ap)
if __name__ == '__main__':
    do_instance_refresh()