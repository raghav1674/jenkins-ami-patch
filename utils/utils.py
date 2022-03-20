#!/usr/bin/python3
import boto3
from datetime import datetime


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


def get_latest_ami_version(client, filters):
    '''
    @purpose: get the latest ami from a region based on filters

    @input: client: boto3.Client
            filters: [{Name: str ,Values:[]}]

    @returns: ImageId: str 

    '''
    if filters:
        images = client.describe_images(Filters=filters)
        if images and len(images['Images']):
            for each_image in images['Images']:
                each_image['CreationDate'] = datetime.strptime(
                    each_image['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
            images['Images'].sort(
                key=lambda image: image['CreationDate'], reverse=True)
            print(images['Images'][0]['ImageId'])
            return images['Images'][0]['ImageId']
    return None


def get_service_ami_version_from_lc(client, service_name):
    '''
    @purpose: get the service ami from a launch configuration based on name

    @input: client: boto3.Client
            service_name: str

    @returns: ImageId: str 
    '''
    if service_name:
        
        launch_configuration_dict = client.describe_launch_configurations(MaxRecords=1)
        next_token = launch_configuration_dict.get('NextToken', None)
        while next_token is not None:
            launch_configurations = client.describe_launch_configurations(
                NextToken=next_token)
            next_token = launch_configurations.get('NextToken', None)
            launch_configuration_dict['LaunchConfigurations'].extend(launch_configurations['LaunchConfigurations'])
        if launch_configuration_dict and len(launch_configuration_dict['LaunchConfigurations']):
            filtered_launch_configurations = list(filter(lambda lc: lc['LaunchConfigurationName'].find(
                service_name) != -1, launch_configuration_dict['LaunchConfigurations']))
            filtered_launch_configurations.sort(
                key=lambda image: image['CreationDate'], reverse=True)
            if len(filtered_launch_configurations):
                return filtered_launch_configurations[0]['ImageId']
    return None


def compare_ami_versions(this_ami, that_ami):
    '''
    @purpose: compare the amis

    @input: this_ami: boto3.Client
            that_ami: str

    @returns: boolean 
    '''
    return this_ami == that_ami
