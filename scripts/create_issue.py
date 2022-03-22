#!/bin/python3
import os
import sys
sys.path.append('.')
from json import loads

from jira.jira import JiraAPI


USERNAME = os.getenv('JIRA_USERNAME')
API_TOKEN = os.getenv("JIRA_API_TOKEN")
FIELD_PATH = os.getenv('FIELD_PATH').split(',')
TARGET_FIELD_VALUE = os.getenv('TARGET_FIELD_VALUE')


jira = JiraAPI(
    USERNAME, API_TOKEN, "config/jira.config.yaml")

details = jira.create_issue()
print(details.key)


