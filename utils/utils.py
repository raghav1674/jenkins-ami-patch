#!/usr/bin/python3
import logging
from time import sleep
import boto3
import os
import botocore


logger = logging.getLogger()
logger.setLevel(logging.INFO)


# status of instance refresh
SUCCESS = 'Successful'
IN_PROGRESS = 'InProgress'
PENDING = 'Pending'

# delay between the calls of instance refresh to check for successful status
DELAY_INTERVAL = os.environ.get('DELAY_INTERVAL') or 59.50


def prepare_boto_clients(services, regions):
    '''
    @purpose: prepare the boto3 clients per region and service

    @input: services: str[], list of services
            regions: str[], list of regions

    @returns: {
        region: {
            'EC2': Boto3.Client('ec2',region)
        }
    }: str 

    '''
    boto3_clients = {}  # list to store the boto3 clients for different services and regions
    for each_region in regions:
        each_client = {}
        for each_service in services:
            each_client[each_service.upper()] = boto3.client(
                each_service.lower(), region_name=each_region)
        boto3_clients[each_region] = each_client
    return boto3_clients


def get_latest_ami_version(client, ssm_parameter_path):
    '''
    @purpose: get the latest ami from a region based on filters

    @input: client: boto3.Client
            ssm_parameter_path: str, (ssm parameter name)

    @returns: ssm Parameter Value: str 

    '''
    parameter = client.get_parameter(Name=ssm_parameter_path)
    return parameter['Parameter']['Value']

   


def get_service_ami_version_from_lc(client, launch_config_name):
    '''
    @purpose: get the service ami from a launch configuration based on name

    @input: client: boto3.Client
            launch_config_name: str

    @returns: ImageId: str 
    '''
    if launch_config_name:
        
        launch_configuration_dict = client.describe_launch_configurations(MaxRecords=1)
        next_token = launch_configuration_dict.get('NextToken', None)
        while next_token is not None:
            launch_configurations = client.describe_launch_configurations(
                NextToken=next_token)
            next_token = launch_configurations.get('NextToken', None)
            launch_configuration_dict['LaunchConfigurations'].extend(launch_configurations['LaunchConfigurations'])
        if launch_configuration_dict and len(launch_configuration_dict['LaunchConfigurations']):
            filtered_launch_configurations = list(filter(lambda lc: lc['LaunchConfigurationName'].find(
                launch_config_name) != -1, launch_configuration_dict['LaunchConfigurations']))
            if len(filtered_launch_configurations):
                return filtered_launch_configurations[0]
    return None


def compare_ami_versions(this_ami, that_ami):
    '''
    @purpose: compare the amis

    @input: this_ami: boto3.Client
            that_ami: str

    @returns: boolean 
    '''
    return this_ami == that_ami


def get_latest_launch_template(client,lt_name):
    
    response = None
    try:
        response = client.describe_launch_template_versions(LaunchTemplateName=lt_name,Versions=["$Latest"])
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'InvalidLaunchTemplateName.NotFoundException':
            response = None 
            print(error)
    except Exception as e:
        response = None
        print(e)
    if(response is None):
        return None
    response = response['LaunchTemplateVersions'][0]['LaunchTemplateData']
    response['LaunchConfigurationName'] = lt_name
    response['SecurityGroups'] = response['SecurityGroupIds']
    return response

def create_new_launch_template(client,old_config,new_ami_id):
    '''
    @purpose: create new launch template with old lc and new ami 

    @input: old_config: Old launch configuration details
            that_ami: new ami id

    @returns: Id of the newly created launch template 
    '''
    lt_name = old_config['LaunchConfigurationName']
    sg_ids = old_config['SecurityGroups']

    if old_config.get('LaunchConfigurationName'): del old_config['LaunchConfigurationName']
    if old_config.get('InstanceMonitoring'): del old_config['InstanceMonitoring']
    if old_config.get('RamdiskId'): del old_config['RamdiskId']
    if old_config.get('ClassicLinkVPCSecurityGroups'): del old_config['ClassicLinkVPCSecurityGroups']
    if old_config.get('KernelId'): del old_config['KernelId']
    del old_config['SecurityGroups']
    if old_config.get('LaunchConfigurationARN'): del old_config['LaunchConfigurationARN']
    if old_config.get('CreatedTime'): del old_config['CreatedTime']
    if old_config.get('BlockDeviceMappings'): del old_config['BlockDeviceMappings']

    old_config['SecurityGroupIds']=sg_ids
    old_config['ImageId'] = new_ami_id

    new_lt_config = {'LaunchTemplateName': lt_name,'LaunchTemplateData':old_config}

    response = None
    try:
        response = client.create_launch_template(**new_lt_config)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'InvalidLaunchTemplateName.AlreadyExistsException':

            response = client.describe_launch_template_versions(LaunchTemplateName=lt_name,Versions=["$Latest"])
            latest_version_number = response['LaunchTemplateVersions'][0]['VersionNumber']
            new_lt_config['SourceVersion'] = str(latest_version_number)
            # create new version of lt 
            response = client.create_launch_template_version(**new_lt_config)
    except Exception as e:
        response = None
        print(e)
    
    if(response is None):
        return None
    return response['LaunchTemplateVersion']['LaunchTemplateId']


    # print(response)

def update_asg_with_new_lt(client,asg_name,lt_id,instance_refresh_preferences):
    '''
    @purpose: update the asg with the newly created lt

    @input: asg: Auto Scaling Group
            lt: Launch Template 

    @returns: Id of the instance refresh 
    '''
    res = client.start_instance_refresh(
        AutoScalingGroupName=asg_name,
        Strategy=instance_refresh_preferences['strategy'],
        Preferences={
            'MinHealthyPercentage': instance_refresh_preferences['min_healthy_percentage'],
            'InstanceWarmup': instance_refresh_preferences['instance_warmup']
        },
        DesiredConfiguration={
            'LaunchTemplate': {
                'LaunchTemplateId': lt_id,
                'Version': '$Latest'
            }
        }
    )

    return res['InstanceRefreshId']

def check_instance_refresh_status(client,asg_name, instance_refresh_id):
    '''
    @purpose: start the instance refresh 

    @input: asg: Auto Scaling Group
            refresh_config: configuration for the asg instance refresh 

    @returns: None 
    '''
    while True:

        instance_refresh_status = client.describe_instance_refreshes(
                                    AutoScalingGroupName=asg_name,
                                    InstanceRefreshIds=[
                                        instance_refresh_id,
                                    ]
                                    )['InstanceRefreshes'][0]['Status']

        if instance_refresh_status in [IN_PROGRESS,PENDING]:

            logger.info(f'Instance Refresh Is In Progress for {asg_name} .....')
        
        elif instance_refresh_status == SUCCESS:
            logger.info(f'Completed Instance Refresh for {asg_name}')
            break
        
        else: 
            logger.warn(f'Some Error Occurred while instance refresh or instance refresh manually cancelled for {asg_name} with instance refresh id {instance_refresh_id}')
            break

        sleep(DELAY_INTERVAL)

  






